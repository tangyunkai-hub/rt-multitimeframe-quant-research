from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

import pandas as pd

from .manifest import ManifestIntegrityError, sha256_file


CONTRACT_SCHEMA = "rtquant-prospective-artifact/v1"
CANDIDATE_ID = "Candidate B"
FREEZE_BOUNDARY_UTC = "2026-09-12T02:00:00+00:00"
FREEZE = pd.Timestamp(FREEZE_BOUNDARY_UTC)

# Public commitments to the exact private frozen bytes. Publishing a digest does
# not publish proprietary rules; it makes later substitution detectable.
FROZEN_PROTOCOL_COMMITMENTS = {
    "candidate_b_engine": "f4e67c6e40aa2d48c4ff780623a7ab0dcf1aa99e9413e473a83c7f9a97876986",
    "candidate_b_forward_preregistration": "54d88cc1b55b7141d4093aa9711bf085e352feb92282747bbe9e545d1ff40c90",
    "forward_initial_state": "2205e8c169504ce60b444c9abd5fd97779459410ea4419219996b1a9da443f15",
    "shadow_event_runner": "3be14121f31e6d05159f55f4625db66082e44537927b1ce3e8ef6867bf8310f2",
    "phase_b_statistics_preregistration": "555c7f4d11721ebe818e30df71d910ce2d6c5c6345460b6dabfa9640cdc0e2be",
    "paired_divergence_evaluator": "ee8b2dc426b40b1f113adca5f6c33fb9e7591c392ac57050aa7a001fee79b2ed",
}

ARTIFACT_KINDS = {
    "candidate_ab_forward_states",
    "candidate_b_paper_bars",
}
ALLOWED_SOURCE_GATE_STATUSES = {
    "PASS",
    "PASS_WITH_EXPECTED_EARLY_WAITING_INTERVALS",
}
FORBIDDEN_PERFORMANCE_TOKENS = (
    "pnl",
    "profit",
    "loss",
    "return",
    "equity",
    "sharpe",
    "drawdown",
    "performance",
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ProspectiveContractError(ManifestIntegrityError):
    """Raised when a prospective artifact violates its frozen provenance contract."""


def _canonical_sha(payload: dict[str, Any]) -> str:
    data = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str
    ).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _require_sha256(value: str, field: str) -> str:
    value = str(value).lower()
    if not _SHA256_RE.fullmatch(value):
        raise ProspectiveContractError(f"{field} must be a lowercase SHA-256 hex digest")
    return value


def _forbidden_columns(columns) -> list[str]:
    bad = []
    for column in columns:
        lowered = str(column).lower()
        if any(token in lowered for token in FORBIDDEN_PERFORMANCE_TOKENS):
            bad.append(str(column))
    return sorted(bad)


def _read_csv(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if frame.empty:
        raise ProspectiveContractError("prospective artifact must contain at least one row")
    return frame


def _validate_timestamps(frame: pd.DataFrame) -> pd.Series:
    if "timestamp" not in frame.columns:
        raise ProspectiveContractError("prospective artifact missing timestamp")
    ts = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
    if ts.isna().any():
        raise ProspectiveContractError("prospective artifact contains invalid timestamp")
    if ts.duplicated().any():
        raise ProspectiveContractError("prospective artifact contains duplicate timestamp")
    if not ts.is_monotonic_increasing:
        raise ProspectiveContractError("prospective artifact timestamps must be monotonic increasing")
    if (ts <= FREEZE).any():
        raise ProspectiveContractError("prospective artifact contains timestamp at/before freeze boundary")
    return ts


def validate_artifact_content(path: str | Path, artifact_kind: str) -> dict[str, Any]:
    if artifact_kind not in ARTIFACT_KINDS:
        raise ProspectiveContractError(f"unsupported artifact kind: {artifact_kind}")
    frame = _read_csv(path)
    ts = _validate_timestamps(frame)

    bad_columns = _forbidden_columns(frame.columns)
    if bad_columns:
        raise ProspectiveContractError(
            f"performance-like columns are embargoed in operational artifact: {bad_columns}"
        )

    if artifact_kind == "candidate_ab_forward_states":
        required = {"timestamp", "A_core", "B_core", "major_bear_epoch_id"}
        missing = required - set(frame.columns)
        if missing:
            raise ProspectiveContractError(f"state ledger missing columns: {sorted(missing)}")
        allowed = {"CORE_LONG", "CORE_SHORT", "FLAT"}
        for column in ("A_core", "B_core"):
            if frame[column].isna().any():
                raise ProspectiveContractError(f"state ledger has missing {column}")
            invalid = set(frame[column].astype(str)) - allowed
            if invalid:
                raise ProspectiveContractError(
                    f"state ledger has invalid {column} values: {sorted(invalid)}"
                )
    else:
        required = {"timestamp", "open", "close", "target_exposure"}
        missing = required - set(frame.columns)
        if missing:
            raise ProspectiveContractError(f"paper-bar artifact missing columns: {sorted(missing)}")
        for column in ("open", "close", "target_exposure"):
            values = pd.to_numeric(frame[column], errors="coerce")
            if values.isna().any() or not values.map(math.isfinite).all():
                raise ProspectiveContractError(f"paper-bar {column} must be finite numeric")
            if column in {"open", "close"} and (values <= 0).any():
                raise ProspectiveContractError(f"paper-bar {column} must be positive")

    return {
        "rows": int(len(frame)),
        "first_timestamp_utc": ts.iloc[0].isoformat(),
        "last_timestamp_utc": ts.iloc[-1].isoformat(),
        "columns": [str(column) for column in frame.columns],
    }


def _load_source_gate(path: str | Path, *, artifact_kind: str) -> dict[str, Any]:
    gate = json.loads(Path(path).read_text(encoding="utf-8"))
    status = gate.get("status")
    if status not in ALLOWED_SOURCE_GATE_STATUSES:
        raise ProspectiveContractError(
            f"source DATA_GATE is not eligible for artifact production: {status!r}"
        )
    if gate.get("performance_evaluation_allowed") is not False:
        raise ProspectiveContractError("source DATA_GATE does not preserve performance embargo")
    if gate.get("candidate_b_judgement_allowed") is not False:
        raise ProspectiveContractError("source DATA_GATE does not preserve Candidate B judgement embargo")

    freeze = pd.Timestamp(gate.get("freeze_boundary_utc_exclusive"))
    freeze = freeze.tz_localize("UTC") if freeze.tzinfo is None else freeze.tz_convert("UTC")
    if freeze != FREEZE:
        raise ProspectiveContractError("source DATA_GATE freeze boundary does not match Candidate B freeze")

    if artifact_kind == "candidate_ab_forward_states":
        if gate.get("mode") != "full":
            raise ProspectiveContractError("formal A/B state ledger requires source DATA_GATE mode=full")
        if gate.get("data_scope") != "FULL_REBUILD_COMPLETE_FORWARD_POOL":
            raise ProspectiveContractError("formal A/B state ledger requires complete forward-pool source scope")

    return gate


def build_prospective_contract(
    *,
    artifact_path: str | Path,
    artifact_kind: str,
    source_manifest_path: str | Path,
    data_gate_path: str | Path,
    source_snapshot_id: str,
    producer_name: str,
    producer_version: str,
    producer_code_sha256: str,
    parent_manifest_sha256: str | None = None,
) -> dict[str, Any]:
    artifact_path = Path(artifact_path)
    if not source_snapshot_id.strip():
        raise ProspectiveContractError("source_snapshot_id must be non-empty")
    if not producer_name.strip() or not producer_version.strip():
        raise ProspectiveContractError("producer name/version must be non-empty")
    producer_code_sha256 = _require_sha256(producer_code_sha256, "producer_code_sha256")
    if parent_manifest_sha256 is not None:
        parent_manifest_sha256 = _require_sha256(parent_manifest_sha256, "parent_manifest_sha256")

    content = validate_artifact_content(artifact_path, artifact_kind)
    gate = _load_source_gate(data_gate_path, artifact_kind=artifact_kind)

    payload = {
        "schema": CONTRACT_SCHEMA,
        "candidate": CANDIDATE_ID,
        "freeze_boundary_utc_exclusive": FREEZE.isoformat(),
        "artifact_kind": artifact_kind,
        "frozen_protocol_commitments": dict(FROZEN_PROTOCOL_COMMITMENTS),
        "artifact": {
            "name": artifact_path.name,
            "sha256": sha256_file(artifact_path),
            "bytes": artifact_path.stat().st_size,
            **content,
        },
        "source": {
            "snapshot_id": source_snapshot_id.strip(),
            "source_manifest_sha256": sha256_file(source_manifest_path),
            "data_gate_sha256": sha256_file(data_gate_path),
            "data_gate_status": gate.get("status"),
            "data_gate_mode": gate.get("mode"),
            "data_scope": gate.get("data_scope"),
            "completed_source_day_end_utc": gate.get("completed_source_day_end_utc"),
        },
        "producer": {
            "name": producer_name.strip(),
            "version": producer_version.strip(),
            "code_sha256": producer_code_sha256,
        },
        "parent_manifest_sha256": parent_manifest_sha256,
        "performance_embargo_active": True,
    }
    payload["manifest_sha256"] = _canonical_sha(payload)
    return payload


def verify_prospective_contract(
    manifest: dict[str, Any],
    *,
    artifact_path: str | Path,
    source_manifest_path: str | Path,
    data_gate_path: str | Path,
    expected_artifact_kind: str | None = None,
    expected_parent_manifest_sha256: str | None = None,
) -> bool:
    declared = manifest.get("manifest_sha256")
    unsigned = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    if not declared or _canonical_sha(unsigned) != declared:
        raise ProspectiveContractError("prospective contract self-hash mismatch")
    if manifest.get("schema") != CONTRACT_SCHEMA:
        raise ProspectiveContractError("prospective contract schema mismatch")
    if manifest.get("candidate") != CANDIDATE_ID:
        raise ProspectiveContractError("prospective contract candidate mismatch")
    if manifest.get("freeze_boundary_utc_exclusive") != FREEZE.isoformat():
        raise ProspectiveContractError("prospective contract freeze boundary mismatch")
    if manifest.get("frozen_protocol_commitments") != FROZEN_PROTOCOL_COMMITMENTS:
        raise ProspectiveContractError("frozen protocol commitment mismatch")

    artifact_kind = manifest.get("artifact_kind")
    if artifact_kind not in ARTIFACT_KINDS:
        raise ProspectiveContractError("prospective contract artifact kind invalid")
    if expected_artifact_kind is not None and artifact_kind != expected_artifact_kind:
        raise ProspectiveContractError("prospective contract artifact kind not expected")

    artifact_path = Path(artifact_path)
    artifact = manifest.get("artifact") or {}
    if artifact.get("name") != artifact_path.name:
        raise ProspectiveContractError("artifact filename mismatch")
    if artifact.get("sha256") != sha256_file(artifact_path):
        raise ProspectiveContractError("artifact SHA-256 mismatch")
    if artifact.get("bytes") != artifact_path.stat().st_size:
        raise ProspectiveContractError("artifact byte-size mismatch")

    content = validate_artifact_content(artifact_path, artifact_kind)
    for field in ("rows", "first_timestamp_utc", "last_timestamp_utc", "columns"):
        if artifact.get(field) != content[field]:
            raise ProspectiveContractError(f"artifact content metadata mismatch: {field}")

    source = manifest.get("source") or {}
    if source.get("source_manifest_sha256") != sha256_file(source_manifest_path):
        raise ProspectiveContractError("source manifest SHA-256 mismatch")
    if source.get("data_gate_sha256") != sha256_file(data_gate_path):
        raise ProspectiveContractError("source DATA_GATE SHA-256 mismatch")
    gate = _load_source_gate(data_gate_path, artifact_kind=artifact_kind)
    if source.get("data_gate_status") != gate.get("status"):
        raise ProspectiveContractError("source DATA_GATE status mismatch")
    if source.get("data_gate_mode") != gate.get("mode"):
        raise ProspectiveContractError("source DATA_GATE mode mismatch")
    if source.get("data_scope") != gate.get("data_scope"):
        raise ProspectiveContractError("source DATA_GATE scope mismatch")
    if not str(source.get("snapshot_id", "")).strip():
        raise ProspectiveContractError("source snapshot id missing")

    producer = manifest.get("producer") or {}
    if not str(producer.get("name", "")).strip() or not str(producer.get("version", "")).strip():
        raise ProspectiveContractError("producer identity missing")
    _require_sha256(producer.get("code_sha256", ""), "producer.code_sha256")

    parent = manifest.get("parent_manifest_sha256")
    if parent is not None:
        _require_sha256(parent, "parent_manifest_sha256")
    if expected_parent_manifest_sha256 is not None:
        expected_parent_manifest_sha256 = _require_sha256(
            expected_parent_manifest_sha256, "expected_parent_manifest_sha256"
        )
        if parent != expected_parent_manifest_sha256:
            raise ProspectiveContractError("parent manifest commitment mismatch")

    if manifest.get("performance_embargo_active") is not True:
        raise ProspectiveContractError("prospective contract must preserve performance embargo")
    return True


def write_contract(manifest: dict[str, Any], path: str | Path) -> None:
    Path(path).write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")


def read_contract(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))

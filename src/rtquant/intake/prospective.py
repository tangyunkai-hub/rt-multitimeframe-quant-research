from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Sequence

from rtquant.repro.manifest import sha256_file
from rtquant.repro.prospective_contract import (
    build_prospective_contract,
    verify_prospective_contract,
    write_contract,
)


BLOCKED_STATUS = "BLOCKED_PROSPECTIVE_SIGNAL_PRODUCER_NOT_FROZEN"
WAITING_STATUS = "WAITING_SOURCE_DATA"
READY_STATUS = "PROSPECTIVE_STATE_ARTIFACT_READY"
EXTERNAL_V3_CLASSIFICATION = "EXTERNAL_HISTORICAL_VALIDATION_NOT_PROSPECTIVE"
FULL_SCOPE = "FULL_REBUILD_COMPLETE_FORWARD_POOL"
ELIGIBLE_GATE_STATUSES = {"PASS", "PASS_WITH_EXPECTED_EARLY_WAITING_INTERVALS"}
WAITING_GATE_STATUSES = {
    "WAITING_NO_COMPLETED_POST_FREEZE_UTC_DAY",
    "WAITING_SOURCE_ARCHIVE_PUBLICATION",
}

# Intentionally empty. The external-history compatibility-v3 adapter is NOT
# prospective authorization. Unlocking this requires a future reviewed Git
# change that freezes a prospective producer before its performance is read.
AUTHORIZED_PROSPECTIVE_SIGNAL_PRODUCER: dict[str, str] | None = None


class ProspectiveIntakeError(RuntimeError):
    """Raised when the prospective intake chain cannot proceed safely."""


def _load_json(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ProspectiveIntakeError(f"expected JSON object: {path}")
    return value


def _embargo_payload(status: str, **extra: Any) -> dict[str, Any]:
    return {
        "status": status,
        "performance": None,
        "performance_embargo_active": True,
        "candidate_b_judgement_allowed": False,
        "broker_route": False,
        **extra,
    }


def validate_full_data_gate(path: str | Path) -> dict[str, Any]:
    gate = _load_json(path)
    if gate.get("performance_evaluation_allowed") is not False:
        raise ProspectiveIntakeError("source DATA_GATE must keep performance disabled")
    if gate.get("candidate_b_judgement_allowed") is not False:
        raise ProspectiveIntakeError("source DATA_GATE must keep Candidate B judgement disabled")
    if gate.get("mode") != "full":
        raise ProspectiveIntakeError("prospective state production requires collector mode=full")
    if gate.get("data_scope") != FULL_SCOPE:
        raise ProspectiveIntakeError("prospective state production requires the complete forward pool")
    return gate


def producer_authorization_is_prospective(authorization: dict[str, Any] | None) -> bool:
    if not authorization:
        return False
    if authorization.get("classification") == EXTERNAL_V3_CLASSIFICATION:
        return False
    return (
        authorization.get("classification") == "V024_PROSPECTIVE_SIGNAL_PRODUCER_FROZEN"
        and authorization.get("candidate") == "Candidate B"
        and authorization.get("freeze_boundary_utc_exclusive") == "2026-09-12T02:00:00+00:00"
        and isinstance(authorization.get("code_sha256"), str)
        and len(authorization["code_sha256"]) == 64
    )


def evaluate_intake_readiness(data_gate_path: str | Path) -> dict[str, Any]:
    gate = validate_full_data_gate(data_gate_path)
    gate_status = gate.get("status")
    if gate_status in WAITING_GATE_STATUSES:
        return _embargo_payload(
            WAITING_STATUS,
            source_gate_status=gate_status,
            next_action="WAIT_FOR_COMPLETE_VERIFIED_SOURCE_DATA",
        )
    if gate_status not in ELIGIBLE_GATE_STATUSES:
        raise ProspectiveIntakeError(f"source DATA_GATE is not eligible: {gate_status!r}")

    if not producer_authorization_is_prospective(AUTHORIZED_PROSPECTIVE_SIGNAL_PRODUCER):
        return _embargo_payload(
            BLOCKED_STATUS,
            source_gate_status=gate_status,
            producer_authorization=None,
            external_compatibility_v3_authorized_for_prospective=False,
            next_action="FREEZE_A_PROSPECTIVE_SIGNAL_PRODUCER_BEFORE_ANY_PERFORMANCE_READ",
        )

    return _embargo_payload(
        "READY_FOR_FROZEN_PRIVATE_PRODUCER",
        source_gate_status=gate_status,
        producer_authorization="FROZEN",
        next_action="RUN_FROZEN_PRIVATE_PRODUCER",
    )


def collector_command(
    *,
    repo_root: str | Path,
    out_dir: str | Path,
    end_date: str | None = None,
) -> list[str]:
    script = Path(repo_root) / "tools" / "download_forward_native_data.py"
    if not script.is_file():
        raise ProspectiveIntakeError(f"forward collector not found: {script}")
    argv = [sys.executable, str(script), "--mode", "full", "--out", str(out_dir)]
    if end_date:
        argv.extend(["--end-date", end_date])
    return argv


def run_full_collection(
    *,
    repo_root: str | Path,
    out_dir: str | Path,
    end_date: str | None = None,
    runner: Callable[..., Any] = subprocess.run,
) -> None:
    result = runner(
        collector_command(repo_root=repo_root, out_dir=out_dir, end_date=end_date),
        check=False,
    )
    if getattr(result, "returncode", 0) != 0:
        raise ProspectiveIntakeError(
            f"full forward collector failed with exit code {result.returncode}"
        )


def _producer_command(producer_path: str | Path, source_dir: Path, state_path: Path) -> list[str]:
    auth = AUTHORIZED_PROSPECTIVE_SIGNAL_PRODUCER
    if not producer_authorization_is_prospective(auth):
        raise ProspectiveIntakeError(BLOCKED_STATUS)
    producer = Path(producer_path)
    if not producer.is_file():
        raise ProspectiveIntakeError(f"private producer not found: {producer}")
    actual = sha256_file(producer)
    if actual != auth["code_sha256"]:
        raise ProspectiveIntakeError("private prospective producer SHA-256 mismatch")
    return [
        sys.executable,
        str(producer),
        "--source-dir",
        str(source_dir),
        "--output",
        str(state_path),
    ]


def run_prospective_intake(
    *,
    repo_root: str | Path,
    runtime_dir: str | Path,
    end_date: str | None = None,
    private_producer: str | Path | None = None,
    collector_runner: Callable[..., Any] = subprocess.run,
    producer_runner: Callable[..., Any] = subprocess.run,
) -> dict[str, Any]:
    runtime = Path(runtime_dir)
    source_dir = runtime / "forward_native_full"
    source_dir.mkdir(parents=True, exist_ok=True)

    run_full_collection(
        repo_root=repo_root,
        out_dir=source_dir,
        end_date=end_date,
        runner=collector_runner,
    )
    gate_path = source_dir / "DATA_GATE.json"
    source_manifest_path = source_dir / "source_manifest.csv"
    readiness = evaluate_intake_readiness(gate_path)
    if readiness["status"] != "READY_FOR_FROZEN_PRIVATE_PRODUCER":
        return readiness

    if private_producer is None:
        raise ProspectiveIntakeError("authorized private producer path is required")
    if not source_manifest_path.is_file():
        raise ProspectiveIntakeError("full collector did not produce source_manifest.csv")

    state_path = runtime / "candidate_b_forward_states.csv"
    command = _producer_command(private_producer, source_dir, state_path)
    result = producer_runner(command, check=False)
    if getattr(result, "returncode", 0) != 0:
        raise ProspectiveIntakeError(
            f"private prospective producer failed with exit code {result.returncode}"
        )
    if not state_path.is_file():
        raise ProspectiveIntakeError("private producer did not create the forward state ledger")

    auth = AUTHORIZED_PROSPECTIVE_SIGNAL_PRODUCER
    source_manifest_sha = sha256_file(source_manifest_path)
    gate_sha = sha256_file(gate_path)
    snapshot_id = hashlib.sha256(
        f"{source_manifest_sha}:{gate_sha}".encode("utf-8")
    ).hexdigest()
    contract = build_prospective_contract(
        artifact_path=state_path,
        artifact_kind="candidate_ab_forward_states",
        source_manifest_path=source_manifest_path,
        data_gate_path=gate_path,
        source_snapshot_id=f"forward-full-{snapshot_id}",
        producer_name=auth["name"],
        producer_version=auth["version"],
        producer_code_sha256=auth["code_sha256"],
    )
    contract_path = runtime / "candidate_b_forward_states.contract.json"
    write_contract(contract, contract_path)
    verify_prospective_contract(
        contract,
        artifact_path=state_path,
        source_manifest_path=source_manifest_path,
        data_gate_path=gate_path,
        expected_artifact_kind="candidate_ab_forward_states",
    )
    return _embargo_payload(
        READY_STATUS,
        state_artifact=str(state_path),
        contract=str(contract_path),
        state_manifest_sha256=contract["manifest_sha256"],
        next_action="RUN_PUBLIC_INFORMATION_GATE_ONLY",
    )

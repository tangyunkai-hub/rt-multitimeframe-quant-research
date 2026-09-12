from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

from rtquant.repro.manifest import sha256_file
from rtquant.repro.prospective_contract import (
    build_prospective_contract,
    verify_prospective_contract,
    write_contract,
)

BLOCKED_STATUS = "BLOCKED_PROSPECTIVE_INPUT_CONTINUITY_NOT_FROZEN"
WAITING_STATUS = "WAITING_SOURCE_DATA"
READY_STATUS = "PROSPECTIVE_STATE_ARTIFACT_READY"
EXTERNAL_V3_CLASSIFICATION = "EXTERNAL_HISTORICAL_VALIDATION_NOT_PROSPECTIVE"
FULL_SCOPE = "FULL_REBUILD_COMPLETE_FORWARD_POOL"
ELIGIBLE_GATE_STATUSES = {"PASS", "PASS_WITH_EXPECTED_EARLY_WAITING_INTERVALS"}
WAITING_GATE_STATUSES = {
    "WAITING_NO_COMPLETED_POST_FREEZE_UTC_DAY",
    "WAITING_SOURCE_ARCHIVE_PUBLICATION",
    "WAITING_FIRST_COMPLETED_STATE_BAR",
}

# Public commitment to private frozen bytes. Publishing a digest does not reveal
# the proprietary signal recipe. Semantic regression used consumed history only.
AUTHORIZED_PROSPECTIVE_SIGNAL_PRODUCER: dict[str, str] = {
    "classification": "V024_PROSPECTIVE_SIGNAL_PRODUCER_FROZEN",
    "candidate": "Candidate B",
    "freeze_boundary_utc_exclusive": "2026-09-12T02:00:00+00:00",
    "name": "v024_prospective_signal_producer_v1",
    "version": "v1",
    "code_sha256": "c2f2a47cf4a22d975a75c922eec3d0cb6d65664180fdf80246b302ac80ed8ceb",
}

# Consumed initialization data only. These commitments came from the successful
# v024-warmup-seed workflow and contain zero prospective evidence rows.
AUTHORIZED_WARMUP_SEED: dict[str, str] = {
    "classification": "V024_CONSUMED_PRE_FREEZE_WARMUP_SEED",
    "freeze_boundary_utc_inclusive": "2026-09-12T02:00:00+00:00",
    "contract_sha256": "a252b31f29bc7604225d482b9ec394c58360145f2ab57368e80860958da33085",
    "seed_root_sha256": "4d5233007551a282164a40cdb34580535454fa07d757666180dc7d83d039589f",
}


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
        raise ProspectiveIntakeError(
            "prospective state production requires collector mode=full"
        )
    if gate.get("data_scope") != FULL_SCOPE:
        raise ProspectiveIntakeError(
            "prospective state production requires the complete forward pool"
        )
    return gate


def validate_bitstamp_state_gate(path: str | Path) -> dict[str, Any]:
    gate = validate_full_data_gate(path)
    if gate.get("classification") != "POST_FREEZE_BITSTAMP_STATE_ONLY_DATA":
        raise ProspectiveIntakeError("Bitstamp state-source classification mismatch")
    if gate.get("state_only") is not True:
        raise ProspectiveIntakeError("Bitstamp source must be state-only")
    if gate.get("price_pnl_use_allowed") is not False:
        raise ProspectiveIntakeError("Bitstamp price/PnL use must remain disabled")
    return gate


def producer_authorization_is_prospective(
    authorization: dict[str, Any] | None,
) -> bool:
    if not authorization or authorization.get("classification") == EXTERNAL_V3_CLASSIFICATION:
        return False
    return (
        authorization.get("classification") == "V024_PROSPECTIVE_SIGNAL_PRODUCER_FROZEN"
        and authorization.get("candidate") == "Candidate B"
        and authorization.get("freeze_boundary_utc_exclusive")
        == "2026-09-12T02:00:00+00:00"
        and isinstance(authorization.get("code_sha256"), str)
        and len(authorization["code_sha256"]) == 64
    )


def _warmup_authorization_is_bound(
    authorization: dict[str, Any] | None,
) -> bool:
    return bool(
        authorization
        and authorization.get("classification")
        == "V024_CONSUMED_PRE_FREEZE_WARMUP_SEED"
        and authorization.get("freeze_boundary_utc_inclusive")
        == "2026-09-12T02:00:00+00:00"
        and isinstance(authorization.get("contract_sha256"), str)
        and len(authorization["contract_sha256"]) == 64
        and isinstance(authorization.get("seed_root_sha256"), str)
        and len(authorization["seed_root_sha256"]) == 64
    )


def validate_warmup_seed(
    warmup_dir: str | Path,
    contract_path: str | Path,
) -> dict[str, Any]:
    if not _warmup_authorization_is_bound(AUTHORIZED_WARMUP_SEED):
        raise ProspectiveIntakeError("frozen warmup seed is not publicly bound")

    warmup = Path(warmup_dir)
    contract_path = Path(contract_path)
    if sha256_file(contract_path) != AUTHORIZED_WARMUP_SEED["contract_sha256"]:
        raise ProspectiveIntakeError("warmup contract SHA-256 mismatch")

    contract = _load_json(contract_path)
    if contract.get("classification") != "V024_CONSUMED_PRE_FREEZE_WARMUP_SEED":
        raise ProspectiveIntakeError("warmup classification mismatch")
    if contract.get("status") != "PASS":
        raise ProspectiveIntakeError("warmup seed did not pass integrity gate")
    if (
        contract.get("candidate_freeze_boundary_utc_inclusive_for_warmup")
        != "2026-09-12T02:00:00+00:00"
    ):
        raise ProspectiveIntakeError("warmup freeze boundary mismatch")
    if (
        contract.get("performance_evaluation_allowed") is not False
        or contract.get("candidate_b_judgement_allowed") is not False
    ):
        raise ProspectiveIntakeError(
            "warmup must preserve performance/judgement embargo"
        )
    if contract.get("prospective_evidence_rows") != 0:
        raise ProspectiveIntakeError("warmup cannot contain prospective evidence rows")
    if contract.get("seed_root_sha256") != AUTHORIZED_WARMUP_SEED["seed_root_sha256"]:
        raise ProspectiveIntakeError("warmup seed-root commitment mismatch")

    for item in contract.get("files", []):
        rel = item.get("path")
        if not rel or ".." in Path(rel).parts:
            raise ProspectiveIntakeError("invalid warmup relative path")
        path = warmup / rel
        if not path.is_file() or sha256_file(path) != item.get("sha256"):
            raise ProspectiveIntakeError(f"warmup file mismatch: {rel}")

    auxiliary_files = {
        "source_request_manifest.csv": contract.get("source_request_manifest_sha256"),
        "integrity.csv": contract.get("integrity_sha256"),
    }
    for rel, expected_sha in auxiliary_files.items():
        path = warmup / rel
        if not path.is_file() or sha256_file(path) != expected_sha:
            raise ProspectiveIntakeError(f"warmup auxiliary file mismatch: {rel}")

    return contract


def evaluate_intake_readiness(
    data_gate_path: str | Path,
    bitstamp_gate_path: str | Path | None = None,
) -> dict[str, Any]:
    gate = validate_full_data_gate(data_gate_path)
    status = gate.get("status")
    if status in WAITING_GATE_STATUSES:
        return _embargo_payload(
            WAITING_STATUS,
            source_gate_status=status,
            next_action="WAIT_FOR_COMPLETE_VERIFIED_SOURCE_DATA",
        )
    if status not in ELIGIBLE_GATE_STATUSES:
        raise ProspectiveIntakeError(f"source DATA_GATE is not eligible: {status!r}")

    if bitstamp_gate_path is None:
        return _embargo_payload(
            BLOCKED_STATUS,
            source_gate_status=status,
            remaining_blockers=["FORWARD_BITSTAMP_STATE_ONLY_SOURCE_CHAIN_NOT_BOUND"],
            next_action="COLLECT_AND_VERIFY_FORWARD_BITSTAMP_STATE_ONLY_DATA",
        )

    bitstamp_gate = validate_bitstamp_state_gate(bitstamp_gate_path)
    bitstamp_status = bitstamp_gate.get("status")
    if bitstamp_status in WAITING_GATE_STATUSES:
        return _embargo_payload(
            WAITING_STATUS,
            source_gate_status=status,
            bitstamp_gate_status=bitstamp_status,
            next_action="WAIT_FOR_COMPLETE_VERIFIED_SOURCE_DATA",
        )
    if bitstamp_status not in ELIGIBLE_GATE_STATUSES:
        raise ProspectiveIntakeError(
            f"Bitstamp DATA_GATE is not eligible: {bitstamp_status!r}"
        )

    if not producer_authorization_is_prospective(
        AUTHORIZED_PROSPECTIVE_SIGNAL_PRODUCER
    ):
        return _embargo_payload(
            BLOCKED_STATUS,
            source_gate_status=status,
            remaining_blockers=["FROZEN_PROSPECTIVE_PRODUCER_NOT_BOUND"],
            next_action="FREEZE_A_PROSPECTIVE_SIGNAL_PRODUCER_BEFORE_ANY_PERFORMANCE_READ",
        )

    if not _warmup_authorization_is_bound(AUTHORIZED_WARMUP_SEED):
        return _embargo_payload(
            BLOCKED_STATUS,
            source_gate_status=status,
            bitstamp_gate_status=bitstamp_status,
            producer_authorization="FROZEN_SEMANTIC_REGRESSION_PASS",
            remaining_blockers=[
                "FROZEN_WARMUP_SEED_THROUGH_CANDIDATE_FREEZE_NOT_YET_BOUND"
            ],
            next_action="FREEZE_AND_BIND_CONSUMED_PRE_FREEZE_WARMUP_SEED",
        )

    return _embargo_payload(
        "READY_FOR_FROZEN_PRIVATE_PRODUCER",
        source_gate_status=status,
        bitstamp_gate_status=bitstamp_status,
        producer_authorization="FROZEN",
        warmup_seed_authorization="FROZEN",
        next_action="RUN_FROZEN_PRIVATE_PRODUCER",
    )


def collector_commands(
    *,
    repo_root: str | Path,
    out_dir: str | Path,
    end_date: str | None = None,
) -> list[list[str]]:
    root = Path(repo_root)
    binance = root / "tools" / "download_forward_native_data.py"
    bitstamp = root / "tools" / "download_forward_bitstamp_state.py"
    for script in (binance, bitstamp):
        if not script.is_file():
            raise ProspectiveIntakeError(f"forward collector not found: {script}")

    commands = []
    for script in (binance, bitstamp):
        argv = [sys.executable, str(script), "--mode", "full", "--out", str(out_dir)]
        if end_date:
            argv.extend(["--end-date", end_date])
        commands.append(argv)
    return commands


def run_full_collection(
    *,
    repo_root: str | Path,
    out_dir: str | Path,
    end_date: str | None = None,
    runner: Callable[..., Any] = subprocess.run,
) -> None:
    for command in collector_commands(
        repo_root=repo_root,
        out_dir=out_dir,
        end_date=end_date,
    ):
        result = runner(command, check=False)
        if getattr(result, "returncode", 0) != 0:
            raise ProspectiveIntakeError(
                "full forward collector failed with exit code "
                f"{result.returncode}: {Path(command[1]).name}"
            )


def _producer_command(
    producer_path: str | Path,
    source_dir: Path,
    state_path: Path,
    warmup_seed: Path,
) -> list[str]:
    authorization = AUTHORIZED_PROSPECTIVE_SIGNAL_PRODUCER
    if not producer_authorization_is_prospective(authorization):
        raise ProspectiveIntakeError(BLOCKED_STATUS)

    producer = Path(producer_path)
    if not producer.is_file():
        raise ProspectiveIntakeError(f"private producer not found: {producer}")
    if sha256_file(producer) != authorization["code_sha256"]:
        raise ProspectiveIntakeError("private prospective producer SHA-256 mismatch")

    return [
        sys.executable,
        str(producer),
        "--source-dir",
        str(source_dir),
        "--warmup-seed",
        str(warmup_seed),
        "--output",
        str(state_path),
    ]


def _write_source_bundle_manifest(
    source_dir: Path,
    warmup_contract: Path,
    producer_sha: str,
) -> Path:
    refs = {
        "binance_source_manifest_sha256": sha256_file(source_dir / "source_manifest.csv"),
        "binance_data_gate_sha256": sha256_file(source_dir / "DATA_GATE.json"),
        "bitstamp_request_manifest_sha256": sha256_file(
            source_dir / "bitstamp" / "request_manifest.csv"
        ),
        "bitstamp_data_gate_sha256": sha256_file(
            source_dir / "bitstamp" / "DATA_GATE.json"
        ),
        "warmup_contract_sha256": sha256_file(warmup_contract),
        "producer_code_sha256": producer_sha,
    }
    path = source_dir / "prospective_source_bundle_manifest.json"
    path.write_text(json.dumps(refs, indent=2, sort_keys=True), encoding="utf-8")
    return path


def run_prospective_intake(
    *,
    repo_root: str | Path,
    runtime_dir: str | Path,
    end_date: str | None = None,
    private_producer: str | Path | None = None,
    warmup_seed: str | Path | None = None,
    warmup_contract: str | Path | None = None,
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
    bitstamp_gate_path = source_dir / "bitstamp" / "DATA_GATE.json"
    readiness = evaluate_intake_readiness(gate_path, bitstamp_gate_path)
    if readiness["status"] != "READY_FOR_FROZEN_PRIVATE_PRODUCER":
        return readiness

    if private_producer is None or warmup_seed is None or warmup_contract is None:
        raise ProspectiveIntakeError(
            "authorized private producer, warmup seed and warmup contract are required"
        )

    warmup_seed_path = Path(warmup_seed)
    warmup_contract_path = Path(warmup_contract)
    validate_warmup_seed(warmup_seed_path, warmup_contract_path)

    state_path = runtime / "candidate_b_forward_states.csv"
    command = _producer_command(
        private_producer,
        source_dir,
        state_path,
        warmup_seed_path,
    )
    result = producer_runner(command, check=False)
    if getattr(result, "returncode", 0) != 0:
        raise ProspectiveIntakeError(
            f"private prospective producer failed with exit code {result.returncode}"
        )
    if not state_path.is_file():
        raise ProspectiveIntakeError(
            "private producer did not create the forward state ledger"
        )

    authorization = AUTHORIZED_PROSPECTIVE_SIGNAL_PRODUCER
    bundle_manifest = _write_source_bundle_manifest(
        source_dir,
        warmup_contract_path,
        authorization["code_sha256"],
    )
    source_manifest_sha = sha256_file(bundle_manifest)
    gate_sha = sha256_file(gate_path)
    snapshot_id = hashlib.sha256(
        f"{source_manifest_sha}:{gate_sha}".encode("utf-8")
    ).hexdigest()

    contract = build_prospective_contract(
        artifact_path=state_path,
        artifact_kind="candidate_ab_forward_states",
        source_manifest_path=bundle_manifest,
        data_gate_path=gate_path,
        source_snapshot_id=f"forward-full-{snapshot_id}",
        producer_name=authorization["name"],
        producer_version=authorization["version"],
        producer_code_sha256=authorization["code_sha256"],
    )
    contract_path = runtime / "candidate_b_forward_states.contract.json"
    write_contract(contract, contract_path)
    verify_prospective_contract(
        contract,
        artifact_path=state_path,
        source_manifest_path=bundle_manifest,
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

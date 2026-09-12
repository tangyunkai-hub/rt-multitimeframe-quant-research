import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from rtquant.intake import prospective as intake


def _gate(path: Path, status="PASS", *, bitstamp=False):
    payload = {
        "status": status,
        "mode": "full",
        "data_scope": "FULL_REBUILD_COMPLETE_FORWARD_POOL",
        "performance_evaluation_allowed": False,
        "candidate_b_judgement_allowed": False,
    }
    if bitstamp:
        payload.update(
            {
                "classification": "POST_FREEZE_BITSTAMP_STATE_ONLY_DATA",
                "state_only": True,
                "price_pnl_use_allowed": False,
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_producer_and_warmup_are_bound_for_ready_source_gates(tmp_path):
    gate = tmp_path / "DATA_GATE.json"
    bitstamp = tmp_path / "bitstamp" / "DATA_GATE.json"
    _gate(gate)
    _gate(bitstamp, bitstamp=True)

    result = intake.evaluate_intake_readiness(gate, bitstamp)

    assert intake.producer_authorization_is_prospective(
        intake.AUTHORIZED_PROSPECTIVE_SIGNAL_PRODUCER
    )
    assert intake._warmup_authorization_is_bound(intake.AUTHORIZED_WARMUP_SEED)
    assert result["status"] == "READY_FOR_FROZEN_PRIVATE_PRODUCER"
    assert result["producer_authorization"] == "FROZEN"
    assert result["warmup_seed_authorization"] == "FROZEN"
    assert result["performance"] is None


def test_external_v3_classification_is_not_prospective_authorization():
    assert (
        intake.producer_authorization_is_prospective(
            {
                "classification": "EXTERNAL_HISTORICAL_VALIDATION_NOT_PROSPECTIVE",
                "candidate": "Candidate B",
                "freeze_boundary_utc_exclusive": "2026-09-12T02:00:00+00:00",
                "code_sha256": "a" * 64,
            }
        )
        is False
    )


def test_bitstamp_gate_must_be_state_only(tmp_path):
    path = tmp_path / "DATA_GATE.json"
    _gate(path, bitstamp=True)
    payload = json.loads(path.read_text())
    payload["price_pnl_use_allowed"] = True
    path.write_text(json.dumps(payload))
    with pytest.raises(intake.ProspectiveIntakeError, match="price/PnL"):
        intake.validate_bitstamp_state_gate(path)


def test_waiting_source_data_does_not_advance(tmp_path):
    gate = tmp_path / "DATA_GATE.json"
    bitstamp = tmp_path / "bitstamp" / "DATA_GATE.json"
    _gate(gate, "PASS")
    _gate(bitstamp, "WAITING_FIRST_COMPLETED_STATE_BAR", bitstamp=True)
    result = intake.evaluate_intake_readiness(gate, bitstamp)
    assert result["status"] == intake.WAITING_STATUS
    assert result["performance"] is None


def test_monitor_gate_is_rejected(tmp_path):
    gate = tmp_path / "DATA_GATE.json"
    _gate(gate)
    payload = json.loads(gate.read_text())
    payload["mode"] = "monitor"
    payload["data_scope"] = "MONITOR_BOUNDED_OVERLAP_NOT_COMPLETE_FORWARD_POOL"
    gate.write_text(json.dumps(payload))
    with pytest.raises(intake.ProspectiveIntakeError, match="mode=full"):
        intake.validate_full_data_gate(gate)


def test_single_command_runs_both_collectors_then_requires_frozen_local_artifacts(tmp_path):
    repo = tmp_path / "repo"
    tools = repo / "tools"
    tools.mkdir(parents=True)
    for name in (
        "download_forward_native_data.py",
        "download_forward_bitstamp_state.py",
    ):
        (tools / name).write_text("# placeholder\n")

    runtime = tmp_path / "runtime"
    calls = []

    def fake(argv, check=False):
        script = Path(argv[1]).name
        calls.append(script)
        out = Path(argv[argv.index("--out") + 1])
        out.mkdir(parents=True, exist_ok=True)
        if script == "download_forward_native_data.py":
            _gate(out / "DATA_GATE.json")
            (out / "source_manifest.csv").write_text("x\n")
        else:
            _gate(out / "bitstamp" / "DATA_GATE.json", bitstamp=True)
            (out / "bitstamp" / "request_manifest.csv").write_text("x\n")
        return SimpleNamespace(returncode=0)

    with pytest.raises(
        intake.ProspectiveIntakeError,
        match="private producer, warmup seed and warmup contract",
    ):
        intake.run_prospective_intake(
            repo_root=repo,
            runtime_dir=runtime,
            end_date="2026-09-30",
            collector_runner=fake,
        )

    assert calls == [
        "download_forward_native_data.py",
        "download_forward_bitstamp_state.py",
    ]
    assert not (runtime / "candidate_b_forward_states.csv").exists()


def test_warmup_seed_tamper_fails_closed(tmp_path, monkeypatch):
    warmup = tmp_path / "warmup"
    (warmup / "binance").mkdir(parents=True)
    data = warmup / "binance" / "BTCUSDT_15m_warmup.csv.gz"
    data.write_bytes(b"frozen-consumed-data")
    request_manifest = warmup / "source_request_manifest.csv"
    request_manifest.write_text("request\n")
    integrity = warmup / "integrity.csv"
    integrity.write_text("status\nPASS\n")

    seed_root = "c" * 64
    contract = {
        "classification": "V024_CONSUMED_PRE_FREEZE_WARMUP_SEED",
        "status": "PASS",
        "candidate_freeze_boundary_utc_inclusive_for_warmup": "2026-09-12T02:00:00+00:00",
        "performance_evaluation_allowed": False,
        "candidate_b_judgement_allowed": False,
        "prospective_evidence_rows": 0,
        "files": [
            {
                "path": "binance/BTCUSDT_15m_warmup.csv.gz",
                "sha256": _sha(data),
                "rows": 1,
            }
        ],
        "seed_root_sha256": seed_root,
        "source_request_manifest_sha256": _sha(request_manifest),
        "integrity_sha256": _sha(integrity),
    }
    contract_path = warmup / "WARMUP_SEED_CONTRACT.json"
    contract_path.write_text(json.dumps(contract, sort_keys=True), encoding="utf-8")

    monkeypatch.setattr(
        intake,
        "AUTHORIZED_WARMUP_SEED",
        {
            "classification": "V024_CONSUMED_PRE_FREEZE_WARMUP_SEED",
            "freeze_boundary_utc_inclusive": "2026-09-12T02:00:00+00:00",
            "contract_sha256": _sha(contract_path),
            "seed_root_sha256": seed_root,
        },
    )

    assert intake.validate_warmup_seed(warmup, contract_path)["status"] == "PASS"
    data.write_bytes(b"tampered")
    with pytest.raises(intake.ProspectiveIntakeError, match="warmup file mismatch"):
        intake.validate_warmup_seed(warmup, contract_path)


def test_cli_has_no_commitment_override_flags():
    from rtquant.intake.cli import build_parser

    help_text = build_parser().format_help()
    for bad in (
        "--producer-sha",
        "--authorize-external-v3",
        "--force-producer",
        "--warmup-sha",
    ):
        assert bad not in help_text

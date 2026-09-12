import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from rtquant.intake import prospective as intake


def _gate(path: Path, status="PASS"):
    path.write_text(json.dumps({
        "status": status,
        "mode": "full",
        "data_scope": "FULL_REBUILD_COMPLETE_FORWARD_POOL",
        "performance_evaluation_allowed": False,
        "candidate_b_judgement_allowed": False,
    }), encoding="utf-8")


def test_current_chain_blocks_when_no_prospective_producer_is_frozen(tmp_path):
    gate = tmp_path / "DATA_GATE.json"
    _gate(gate)
    result = intake.evaluate_intake_readiness(gate)
    assert result["status"] == intake.BLOCKED_STATUS
    assert result["performance"] is None
    assert result["performance_embargo_active"] is True
    assert result["external_compatibility_v3_authorized_for_prospective"] is False


def test_external_v3_classification_is_explicitly_not_prospective_authorization():
    assert intake.producer_authorization_is_prospective({
        "classification": "EXTERNAL_HISTORICAL_VALIDATION_NOT_PROSPECTIVE",
        "candidate": "Candidate B",
        "freeze_boundary_utc_exclusive": "2026-09-12T02:00:00+00:00",
        "code_sha256": "a" * 64,
    }) is False


def test_waiting_source_data_does_not_advance_to_producer(tmp_path):
    gate = tmp_path / "DATA_GATE.json"
    _gate(gate, "WAITING_SOURCE_ARCHIVE_PUBLICATION")
    result = intake.evaluate_intake_readiness(gate)
    assert result["status"] == intake.WAITING_STATUS
    assert result["next_action"] == "WAIT_FOR_COMPLETE_VERIFIED_SOURCE_DATA"


def test_monitor_gate_is_rejected_for_formal_state_production(tmp_path):
    gate = tmp_path / "DATA_GATE.json"
    _gate(gate)
    value = json.loads(gate.read_text())
    value["mode"] = "monitor"
    value["data_scope"] = "MONITOR_BOUNDED_OVERLAP_NOT_COMPLETE_FORWARD_POOL"
    gate.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(intake.ProspectiveIntakeError, match="mode=full"):
        intake.evaluate_intake_readiness(gate)


def test_single_command_runs_full_collector_then_stops_before_unfrozen_producer(tmp_path):
    repo = tmp_path / "repo"
    tools = repo / "tools"
    tools.mkdir(parents=True)
    (tools / "download_forward_native_data.py").write_text("# placeholder\n", encoding="utf-8")
    runtime = tmp_path / "runtime"

    calls = []
    def fake_collector(argv, check=False):
        calls.append(argv)
        out_dir = Path(argv[argv.index("--out") + 1])
        out_dir.mkdir(parents=True, exist_ok=True)
        _gate(out_dir / "DATA_GATE.json")
        (out_dir / "source_manifest.csv").write_text("source,status\nx,OK\n", encoding="utf-8")
        return SimpleNamespace(returncode=0)

    result = intake.run_prospective_intake(
        repo_root=repo,
        runtime_dir=runtime,
        end_date="2026-09-30",
        collector_runner=fake_collector,
    )
    assert result["status"] == intake.BLOCKED_STATUS
    assert "--mode" in calls[0]
    assert calls[0][calls[0].index("--mode") + 1] == "full"
    assert not (runtime / "candidate_b_forward_states.csv").exists()


def test_cli_has_no_flag_to_override_producer_commitment():
    from rtquant.intake.cli import build_parser
    help_text = build_parser().format_help()
    assert "--producer-sha" not in help_text
    assert "--authorize-external-v3" not in help_text
    assert "--force-producer" not in help_text

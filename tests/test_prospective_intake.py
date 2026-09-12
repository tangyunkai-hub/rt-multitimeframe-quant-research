import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from rtquant.intake import prospective as intake


def _gate(path: Path,status="PASS",*,bitstamp=False):
    payload={"status":status,"mode":"full","data_scope":"FULL_REBUILD_COMPLETE_FORWARD_POOL",
             "performance_evaluation_allowed":False,"candidate_b_judgement_allowed":False}
    if bitstamp:
        payload.update({"classification":"POST_FREEZE_BITSTAMP_STATE_ONLY_DATA","state_only":True,"price_pnl_use_allowed":False})
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(payload),encoding="utf-8")


def test_producer_is_now_frozen_but_warmup_binding_still_blocks(tmp_path):
    g=tmp_path/"DATA_GATE.json"; b=tmp_path/"bitstamp"/"DATA_GATE.json"; _gate(g); _gate(b,bitstamp=True)
    result=intake.evaluate_intake_readiness(g,b)
    assert intake.producer_authorization_is_prospective(intake.AUTHORIZED_PROSPECTIVE_SIGNAL_PRODUCER)
    assert result["status"]==intake.BLOCKED_STATUS
    assert result["producer_authorization"]=="FROZEN_SEMANTIC_REGRESSION_PASS"
    assert result["remaining_blockers"]==["FROZEN_WARMUP_SEED_THROUGH_CANDIDATE_FREEZE_NOT_YET_BOUND"]
    assert result["performance"] is None


def test_external_v3_classification_is_not_prospective_authorization():
    assert intake.producer_authorization_is_prospective({"classification":"EXTERNAL_HISTORICAL_VALIDATION_NOT_PROSPECTIVE",
        "candidate":"Candidate B","freeze_boundary_utc_exclusive":"2026-09-12T02:00:00+00:00","code_sha256":"a"*64}) is False


def test_bitstamp_gate_must_be_state_only(tmp_path):
    p=tmp_path/"DATA_GATE.json"; _gate(p,bitstamp=True); x=json.loads(p.read_text()); x["price_pnl_use_allowed"]=True; p.write_text(json.dumps(x))
    with pytest.raises(intake.ProspectiveIntakeError,match="price/PnL"):
        intake.validate_bitstamp_state_gate(p)


def test_waiting_source_data_does_not_advance(tmp_path):
    g=tmp_path/"DATA_GATE.json"; b=tmp_path/"bitstamp"/"DATA_GATE.json"; _gate(g,"PASS"); _gate(b,"WAITING_FIRST_COMPLETED_STATE_BAR",bitstamp=True)
    r=intake.evaluate_intake_readiness(g,b); assert r["status"]==intake.WAITING_STATUS


def test_monitor_gate_is_rejected(tmp_path):
    g=tmp_path/"DATA_GATE.json"; _gate(g); x=json.loads(g.read_text()); x["mode"]="monitor"; x["data_scope"]="MONITOR_BOUNDED_OVERLAP_NOT_COMPLETE_FORWARD_POOL"; g.write_text(json.dumps(x))
    with pytest.raises(intake.ProspectiveIntakeError,match="mode=full"): intake.validate_full_data_gate(g)


def test_single_command_runs_both_collectors_then_stops_at_warmup_gate(tmp_path):
    repo=tmp_path/"repo"; tools=repo/"tools"; tools.mkdir(parents=True)
    for name in ("download_forward_native_data.py","download_forward_bitstamp_state.py"):(tools/name).write_text("# placeholder\n")
    runtime=tmp_path/"runtime"; calls=[]
    def fake(argv,check=False):
        calls.append(Path(argv[1]).name); out=Path(argv[argv.index("--out")+1]); out.mkdir(parents=True,exist_ok=True)
        if Path(argv[1]).name=="download_forward_native_data.py":
            _gate(out/"DATA_GATE.json"); (out/"source_manifest.csv").write_text("x\n")
        else:
            _gate(out/"bitstamp"/"DATA_GATE.json",bitstamp=True); (out/"bitstamp"/"request_manifest.csv").write_text("x\n")
        return SimpleNamespace(returncode=0)
    r=intake.run_prospective_intake(repo_root=repo,runtime_dir=runtime,end_date="2026-09-30",collector_runner=fake)
    assert calls==["download_forward_native_data.py","download_forward_bitstamp_state.py"]
    assert r["status"]==intake.BLOCKED_STATUS
    assert not (runtime/"candidate_b_forward_states.csv").exists()


def test_cli_has_no_commitment_override_flags():
    from rtquant.intake.cli import build_parser
    help_text=build_parser().format_help()
    for bad in ("--producer-sha","--authorize-external-v3","--force-producer","--warmup-sha"):
        assert bad not in help_text

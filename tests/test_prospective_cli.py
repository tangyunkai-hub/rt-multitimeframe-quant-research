import json

import pandas as pd

from rtquant.repro.prospective_contract import (
    build_prospective_contract,
    write_contract,
)
from rtquant.validation import cli
from rtquant.validation.prospective import CANDIDATE_B_FREEZE_UTC


PRODUCER_SHA = "a" * 64


def _write_csv(path, rows):
    pd.DataFrame(rows).to_csv(path, index=False)


def _contract_args(tmp_path, state_path):
    source_manifest = tmp_path / "source_manifest.csv"
    source_manifest.write_text("source,sha256\ndaily,abc\n", encoding="utf-8")
    data_gate = tmp_path / "DATA_GATE.json"
    data_gate.write_text(json.dumps({
        "status": "PASS",
        "mode": "full",
        "data_scope": "FULL_REBUILD_COMPLETE_FORWARD_POOL",
        "freeze_boundary_utc_exclusive": "2026-09-12T02:00:00+00:00",
        "completed_source_day_end_utc": "2027-04-01",
        "performance_evaluation_allowed": False,
        "candidate_b_judgement_allowed": False,
    }), encoding="utf-8")
    manifest = build_prospective_contract(
        artifact_path=state_path,
        artifact_kind="candidate_ab_forward_states",
        source_manifest_path=source_manifest,
        data_gate_path=data_gate,
        source_snapshot_id="full-forward-snapshot-001",
        producer_name="private-frozen-shadow-engine",
        producer_version="v0.24",
        producer_code_sha256=PRODUCER_SHA,
    )
    manifest_path = tmp_path / "states.contract.json"
    write_contract(manifest, manifest_path)
    return [
        "--input", str(state_path),
        "--manifest", str(manifest_path),
        "--source-manifest", str(source_manifest),
        "--data-gate", str(data_gate),
    ], manifest


def test_cli_keeps_performance_embargoed_before_information_floor(tmp_path, capsys):
    path = tmp_path / "forward_states.csv"
    _write_csv(path, [
        {
            "timestamp": "2026-09-13T02:00:00Z",
            "A_core": "CORE_SHORT",
            "B_core": "CORE_SHORT",
            "major_bear_epoch_id": None,
        },
        {
            "timestamp": "2026-09-14T02:00:00Z",
            "A_core": "CORE_SHORT",
            "B_core": "FLAT",
            "major_bear_epoch_id": "bear-1",
        },
    ])
    args, manifest = _contract_args(tmp_path, path)

    code = cli.main(args)
    payload = json.loads(capsys.readouterr().out)

    assert code == 0
    assert payload["classification"] == "CANDIDATE_B_PROSPECTIVE_INFORMATION_GATE_ONLY"
    assert payload["performance"] is None
    assert payload["next_action"] == "KEEP_PERFORMANCE_EMBARGOED"
    assert payload["information_floor"]["performance_release_allowed"] is False
    assert payload["provenance"]["status"] == "VERIFIED"
    assert payload["provenance"]["manifest_sha256"] == manifest["manifest_sha256"]


def test_cli_can_authorize_only_the_separately_frozen_private_evaluator(tmp_path, capsys):
    freeze = CANDIDATE_B_FREEZE_UTC
    rows = []
    divergent_index = 0
    for i in range(13):
        divergent = i % 2 == 1
        epoch = None
        if divergent:
            epoch = f"bear-{divergent_index // 2 + 1}"
            divergent_index += 1
        rows.append({
            "timestamp": (freeze + pd.Timedelta(days=1 + i * 20)).isoformat(),
            "A_core": "CORE_SHORT",
            "B_core": "FLAT" if divergent else "CORE_SHORT",
            "major_bear_epoch_id": epoch,
        })

    path = tmp_path / "eligible.csv"
    _write_csv(path, rows)
    args, _ = _contract_args(tmp_path, path)
    code = cli.main(args)
    payload = json.loads(capsys.readouterr().out)

    assert code == 0
    floor = payload["information_floor"]
    assert floor["forward_days"] >= 180
    assert floor["divergence_segments"] == 6
    assert floor["independent_major_bear_epochs"] == 3
    assert floor["performance_release_allowed"] is True
    assert payload["performance"] is None
    assert payload["next_action"] == "RUN_SEPARATELY_FROZEN_PRIVATE_V024_EVALUATOR"
    assert payload["provenance"]["status"] == "VERIFIED"


def test_cli_rejects_artifact_changed_after_contract(tmp_path, capsys):
    path = tmp_path / "states.csv"
    _write_csv(path, [{
        "timestamp": "2026-09-13T04:00:00Z",
        "A_core": "CORE_SHORT",
        "B_core": "FLAT",
        "major_bear_epoch_id": "bear-1",
    }])
    args, _ = _contract_args(tmp_path, path)
    frame = pd.read_csv(path)
    frame.loc[0, "timestamp"] = CANDIDATE_B_FREEZE_UTC.isoformat()
    frame.to_csv(path, index=False)

    code = cli.main(args)
    payload = json.loads(capsys.readouterr().out)

    assert code == 2
    assert payload["status"] == "ERROR"
    assert payload["performance"] is None
    assert payload["provenance_verified"] is False
    assert "SHA-256 mismatch" in payload["message"]


def test_cli_does_not_expose_threshold_override_flags():
    help_text = cli.build_parser().format_help()
    assert "--min-forward" not in help_text
    assert "--min-divergence" not in help_text
    assert "--min-major" not in help_text
    assert "--manifest" in help_text
    assert "--source-manifest" in help_text
    assert "--data-gate" in help_text

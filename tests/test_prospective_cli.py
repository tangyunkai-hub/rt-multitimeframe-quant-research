import json

import pandas as pd

from rtquant.validation import cli
from rtquant.validation.prospective import CANDIDATE_B_FREEZE_UTC


def _write_csv(path, rows):
    pd.DataFrame(rows).to_csv(path, index=False)


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

    code = cli.main(["--input", str(path)])
    payload = json.loads(capsys.readouterr().out)

    assert code == 0
    assert payload["classification"] == "CANDIDATE_B_PROSPECTIVE_INFORMATION_GATE_ONLY"
    assert payload["performance"] is None
    assert payload["next_action"] == "KEEP_PERFORMANCE_EMBARGOED"
    assert payload["information_floor"]["performance_release_allowed"] is False


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
    code = cli.main(["--input", str(path)])
    payload = json.loads(capsys.readouterr().out)

    assert code == 0
    floor = payload["information_floor"]
    assert floor["forward_days"] >= 180
    assert floor["divergence_segments"] == 6
    assert floor["independent_major_bear_epochs"] == 3
    assert floor["performance_release_allowed"] is True
    assert payload["performance"] is None
    assert payload["next_action"] == "RUN_SEPARATELY_FROZEN_PRIVATE_V024_EVALUATOR"


def test_cli_rejects_observations_at_or_before_freeze(tmp_path, capsys):
    path = tmp_path / "bad.csv"
    _write_csv(path, [{
        "timestamp": CANDIDATE_B_FREEZE_UTC.isoformat(),
        "A_core": "CORE_SHORT",
        "B_core": "CORE_SHORT",
        "major_bear_epoch_id": None,
    }])

    code = cli.main(["--input", str(path)])
    payload = json.loads(capsys.readouterr().out)

    assert code == 2
    assert payload["status"] == "ERROR"
    assert payload["performance"] is None
    assert "at/before freeze boundary" in payload["message"]


def test_cli_does_not_expose_threshold_override_flags():
    help_text = cli.build_parser().format_help()
    assert "--min-forward" not in help_text
    assert "--min-divergence" not in help_text
    assert "--min-major" not in help_text

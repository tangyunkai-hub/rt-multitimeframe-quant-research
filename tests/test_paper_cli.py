import json

import pandas as pd

from rtquant.paper import cli


ROWS = [
    {"timestamp": "2026-10-01T00:00:00Z", "open": 100.0, "close": 101.0, "target_exposure": 1.0},
    {"timestamp": "2026-10-01T00:15:00Z", "open": 102.0, "close": 104.0, "target_exposure": 0.4},
]


def _write_csv(path, rows):
    pd.DataFrame(rows).to_csv(path, index=False)


def test_ingest_cli_never_releases_performance_fields(tmp_path, capsys):
    journal = tmp_path / "paper.jsonl"
    source = tmp_path / "bars.csv"
    _write_csv(source, ROWS)

    code = cli.main([
        "ingest",
        "--journal", str(journal),
        "--input", str(source),
        "--fee-bps-one-way", "7",
        "--slippage-bps-one-way", "2",
    ])
    output = capsys.readouterr().out
    payload = json.loads(output)

    assert code == 0
    assert payload["status"] == "OK"
    assert payload["mode"] == "BROKERLESS_PAPER_ONLY"
    assert payload["broker_route"] is False
    assert payload["performance_embargo_active"] is True
    assert payload["performance_fields_released"] is False
    assert payload["processed_rows"] == 2
    assert payload["health"]["journal_seq"] == 2
    assert "equity" not in output.lower()
    assert "turnover" not in output.lower()
    assert "pnl" not in output.lower()
    assert "return" not in output.lower()


def test_status_cli_verifies_idle_journal_without_equity(tmp_path, capsys):
    journal = tmp_path / "paper.jsonl"
    source = tmp_path / "bars.jsonl"
    source.write_text("\n".join(json.dumps(row) for row in ROWS) + "\n", encoding="utf-8")

    assert cli.main(["ingest", "--journal", str(journal), "--input", str(source)]) == 0
    capsys.readouterr()

    code = cli.main(["status", "--journal", str(journal)])
    output = capsys.readouterr().out
    payload = json.loads(output)

    assert code == 0
    assert payload["status"] == "VERIFIED_IDLE"
    assert payload["journal_seq"] == 2
    assert payload["broker_route"] is False
    assert payload["performance_embargo_active"] is True
    assert payload["performance_fields_released"] is False
    assert "equity" not in output.lower()
    assert "pnl" not in output.lower()
    assert "return" not in output.lower()


def test_retrying_last_bar_is_idempotent_through_cli(tmp_path, capsys):
    journal = tmp_path / "paper.jsonl"
    initial = tmp_path / "initial.csv"
    retry = tmp_path / "retry.csv"
    _write_csv(initial, ROWS)
    _write_csv(retry, [ROWS[-1]])

    assert cli.main(["ingest", "--journal", str(journal), "--input", str(initial)]) == 0
    capsys.readouterr()

    code = cli.main(["ingest", "--journal", str(journal), "--input", str(retry)])
    payload = json.loads(capsys.readouterr().out)

    assert code == 0
    assert payload["processed_rows"] == 0
    assert payload["idempotent_rows"] == 1
    assert payload["health"]["journal_seq"] == 2
    assert payload["actions"] == [{"status": "IDEMPOTENT_NOOP"}]


def test_invalid_numeric_input_fails_before_journal_creation(tmp_path, capsys):
    journal = tmp_path / "paper.jsonl"
    source = tmp_path / "bad.csv"
    _write_csv(source, [{
        "timestamp": "2026-10-01T00:00:00Z",
        "open": 100.0,
        "close": 101.0,
        "target_exposure": float("nan"),
    }])

    code = cli.main(["ingest", "--journal", str(journal), "--input", str(source)])
    payload = json.loads(capsys.readouterr().out)

    assert code == 2
    assert payload["status"] == "ERROR"
    assert payload["performance_fields_released"] is False
    assert payload["broker_route"] is False
    assert not journal.exists()


def test_redacted_health_is_allowlist_not_blacklist():
    payload = cli.redacted_health({
        "status": "ACTIVE",
        "journal_seq": 4,
        "equity": 9.99,
        "pnl": 123,
        "future_performance_metric": 456,
        "broker_route": False,
    })

    assert payload["journal_seq"] == 4
    assert payload["performance_fields_released"] is False
    assert "equity" not in payload
    assert "pnl" not in payload
    assert "future_performance_metric" not in payload

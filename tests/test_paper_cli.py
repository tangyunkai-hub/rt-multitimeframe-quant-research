import json

import pandas as pd

from rtquant.paper import cli
from rtquant.repro.prospective_contract import (
    build_prospective_contract,
    write_contract,
)


ROWS = [
    {"timestamp": "2026-10-01T00:00:00Z", "open": 100.0, "close": 101.0, "target_exposure": 1.0},
    {"timestamp": "2026-10-01T00:15:00Z", "open": 102.0, "close": 104.0, "target_exposure": 0.4},
]
PARENT_SHA = "b" * 64
PRODUCER_SHA = "c" * 64


def _write_csv(path, rows):
    pd.DataFrame(rows).to_csv(path, index=False)


def _contract_args(tmp_path, source, *, stem):
    source_manifest = tmp_path / f"{stem}.source_manifest.csv"
    source_manifest.write_text("source,sha256\ndaily,abc\n", encoding="utf-8")
    data_gate = tmp_path / f"{stem}.DATA_GATE.json"
    data_gate.write_text(json.dumps({
        "status": "PASS",
        "mode": "monitor",
        "data_scope": "MONITOR_BOUNDED_OVERLAP_NOT_COMPLETE_FORWARD_POOL",
        "freeze_boundary_utc_exclusive": "2026-09-12T02:00:00+00:00",
        "completed_source_day_end_utc": "2026-10-01",
        "performance_evaluation_allowed": False,
        "candidate_b_judgement_allowed": False,
    }), encoding="utf-8")
    manifest = build_prospective_contract(
        artifact_path=source,
        artifact_kind="candidate_b_paper_bars",
        source_manifest_path=source_manifest,
        data_gate_path=data_gate,
        source_snapshot_id=f"monitor-{stem}",
        producer_name="private-paper-input-builder",
        producer_version="v0.28",
        producer_code_sha256=PRODUCER_SHA,
        parent_manifest_sha256=PARENT_SHA,
    )
    manifest_path = tmp_path / f"{stem}.contract.json"
    write_contract(manifest, manifest_path)
    return [
        "--manifest", str(manifest_path),
        "--source-manifest", str(source_manifest),
        "--data-gate", str(data_gate),
        "--expected-parent-manifest-sha256", PARENT_SHA,
    ], manifest


def _ingest_args(tmp_path, journal, source, *, stem):
    contract_args, manifest = _contract_args(tmp_path, source, stem=stem)
    return [
        "ingest",
        "--journal", str(journal),
        "--input", str(source),
        *contract_args,
    ], manifest


def test_ingest_cli_verifies_provenance_and_never_releases_performance_fields(tmp_path, capsys):
    journal = tmp_path / "paper.jsonl"
    source = tmp_path / "bars.csv"
    _write_csv(source, ROWS)
    args, manifest = _ingest_args(tmp_path, journal, source, stem="initial")
    args += ["--fee-bps-one-way", "7", "--slippage-bps-one-way", "2"]

    code = cli.main(args)
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
    assert payload["provenance"]["status"] == "VERIFIED"
    assert payload["provenance"]["manifest_sha256"] == manifest["manifest_sha256"]
    assert "equity" not in output.lower()
    assert "turnover" not in output.lower()
    assert "pnl" not in output.lower()
    assert "return" not in output.lower()


def test_status_cli_verifies_idle_journal_without_equity(tmp_path, capsys):
    journal = tmp_path / "paper.jsonl"
    source = tmp_path / "bars.csv"
    _write_csv(source, ROWS)
    args, _ = _ingest_args(tmp_path, journal, source, stem="status")
    assert cli.main(args) == 0
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


def test_retrying_last_bar_is_idempotent_through_strict_cli(tmp_path, capsys):
    journal = tmp_path / "paper.jsonl"
    initial = tmp_path / "initial.csv"
    retry = tmp_path / "retry.csv"
    _write_csv(initial, ROWS)
    _write_csv(retry, [ROWS[-1]])

    initial_args, _ = _ingest_args(tmp_path, journal, initial, stem="initial_retry")
    assert cli.main(initial_args) == 0
    capsys.readouterr()

    retry_args, _ = _ingest_args(tmp_path, journal, retry, stem="retry")
    code = cli.main(retry_args)
    payload = json.loads(capsys.readouterr().out)

    assert code == 0
    assert payload["processed_rows"] == 0
    assert payload["idempotent_rows"] == 1
    assert payload["health"]["journal_seq"] == 2
    assert payload["actions"] == [{"status": "IDEMPOTENT_NOOP"}]


def test_tampered_input_fails_contract_before_journal_creation(tmp_path, capsys):
    journal = tmp_path / "paper.jsonl"
    source = tmp_path / "bars.csv"
    _write_csv(source, ROWS)
    args, _ = _ingest_args(tmp_path, journal, source, stem="tamper")
    frame = pd.read_csv(source)
    frame.loc[0, "target_exposure"] = float("nan")
    frame.to_csv(source, index=False)

    code = cli.main(args)
    payload = json.loads(capsys.readouterr().out)

    assert code == 2
    assert payload["status"] == "ERROR"
    assert payload["performance_fields_released"] is False
    assert payload["broker_route"] is False
    assert payload["provenance_verified"] is False
    assert "SHA-256 mismatch" in payload["message"]
    assert not journal.exists()


def test_wrong_parent_commitment_fails_before_journal_creation(tmp_path, capsys):
    journal = tmp_path / "paper.jsonl"
    source = tmp_path / "bars.csv"
    _write_csv(source, ROWS)
    args, _ = _ingest_args(tmp_path, journal, source, stem="wrong_parent")
    index = args.index("--expected-parent-manifest-sha256") + 1
    args[index] = "d" * 64

    code = cli.main(args)
    payload = json.loads(capsys.readouterr().out)

    assert code == 2
    assert payload["status"] == "ERROR"
    assert payload["provenance_verified"] is False
    assert "parent manifest commitment mismatch" in payload["message"]
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

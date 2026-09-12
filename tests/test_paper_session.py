import json
import os
import socket
import pandas as pd
import pytest

from rtquant.execution import simulate_next_open
from rtquant.paper import (
    JournalIntegrityError,
    PaperSession,
    SessionLockError,
    replay_journal,
)

ROWS = [
    {"timestamp":"2026-10-01T00:00:00Z","open":100.0,"close":101.0,"target_exposure":1.0},
    {"timestamp":"2026-10-01T00:15:00Z","open":102.0,"close":104.0,"target_exposure":1.0},
    {"timestamp":"2026-10-01T00:30:00Z","open":103.0,"close":102.0,"target_exposure":0.4},
    {"timestamp":"2026-10-01T00:45:00Z","open":101.0,"close":100.0,"target_exposure":0.0},
]


def test_session_restart_matches_batch_execution(tmp_path):
    journal = tmp_path / "paper.jsonl"
    with PaperSession(journal, fee_bps_one_way=7, slippage_bps_one_way=2) as s:
        actions = s.ingest_many(ROWS[:2])
        assert [a["status"] for a in actions] == ["PROCESSED", "PROCESSED"]
        first_health = s.health()
        assert first_health["journal_seq"] == 2
        assert first_health["broker_route"] is False

    with PaperSession(journal, fee_bps_one_way=7, slippage_bps_one_way=2) as s:
        assert s.health()["journal_seq"] == 2
        s.ingest_many(ROWS[2:])
        final = s.state

    batch = simulate_next_open(
        pd.DataFrame(ROWS), fee_bps_one_way=7, slippage_bps_one_way=2
    )
    assert final.equity == pytest.approx(batch["equity"].iloc[-1])
    assert replay_journal(journal) == final


def test_single_writer_lock_rejects_second_session(tmp_path):
    journal = tmp_path / "paper.jsonl"
    with PaperSession(journal):
        with pytest.raises(SessionLockError, match="writer lock"):
            with PaperSession(journal):
                pass


def test_stale_same_host_lock_requires_explicit_recovery(tmp_path):
    journal = tmp_path / "paper.jsonl"
    lock = journal.with_suffix(journal.suffix + ".lock")
    lock.write_text(json.dumps({
        "schema_version": 1,
        "session_id": "dead",
        "token": "dead",
        "pid": 999999999,
        "hostname": socket.gethostname(),
        "journal": journal.name,
        "acquired_at_utc": "2026-01-01T00:00:00+00:00",
    }) + "\n")

    with pytest.raises(SessionLockError):
        with PaperSession(journal):
            pass

    with PaperSession(journal, recover_stale_lock=True) as s:
        assert s.health()["journal_seq"] == 0


def test_out_of_band_journal_change_forces_recovery(tmp_path):
    journal = tmp_path / "paper.jsonl"
    with PaperSession(journal) as s:
        s.ingest(ROWS[0])
        with journal.open("a", encoding="utf-8") as f:
            f.write("{}\n")
        with pytest.raises(JournalIntegrityError, match="changed after recovery"):
            s.ingest(ROWS[1])

    with pytest.raises(JournalIntegrityError):
        replay_journal(journal)


def test_checkpoint_is_non_authoritative_cache(tmp_path):
    journal = tmp_path / "paper.jsonl"
    with PaperSession(journal) as s:
        s.ingest(ROWS[0])
        checkpoint = json.loads(s.checkpoint_path.read_text())
        assert checkpoint["authoritative"] is False
        assert checkpoint["journal_seq"] == 1
        assert checkpoint["state_hash"] == s.state.digest()

    # Corrupting the cache must not alter journal recovery.
    checkpoint_path = journal.with_suffix(journal.suffix + ".checkpoint.json")
    checkpoint_path.write_text('{"equity":999}\n')
    with PaperSession(journal) as s:
        assert s.health()["journal_seq"] == 1
        assert s.state.equity != 999


def test_idempotent_retry_does_not_advance_session_seq(tmp_path):
    journal = tmp_path / "paper.jsonl"
    with PaperSession(journal) as s:
        s.ingest(ROWS[0])
        seq = s.health()["journal_seq"]
        action = s.ingest({
            "timestamp":"2026-10-01T00:00:00+00:00",
            "open":100,
            "close":101,
            "target_exposure":1,
        })
        assert action["status"] == "IDEMPOTENT_NOOP"
        assert s.health()["journal_seq"] == seq
        assert s.health()["idempotent_retries_this_session"] == 1


def test_session_lifecycle_log_records_start_and_stop(tmp_path):
    journal = tmp_path / "paper.jsonl"
    with PaperSession(journal) as s:
        s.ingest(ROWS[0])
        sessions_path = s.sessions_path

    events = [json.loads(line)["event"] for line in sessions_path.read_text().splitlines()]
    assert events == ["STARTED", "STOPPED"]

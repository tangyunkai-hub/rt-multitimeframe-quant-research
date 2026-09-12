import json
import pytest

from rtquant.paper import (
    JournalIntegrityError,
    PaperState,
    process_and_append,
    process_bar,
    replay_journal,
)

ROWS = [
    {"timestamp":"2026-10-01T00:00:00Z","open":100,"close":101,"target_exposure":1},
    {"timestamp":"2026-10-01T00:15:00Z","open":102,"close":103,"target_exposure":1},
    {"timestamp":"2026-10-01T00:30:00Z","open":104,"close":102,"target_exposure":0},
]


def test_restart_recovery_matches_uninterrupted(tmp_path):
    journal = tmp_path / "paper.jsonl"
    state = PaperState()
    for row in ROWS[:2]:
        state, _ = process_and_append(journal, state, row)

    restarted = replay_journal(journal)
    restarted, _ = process_and_append(journal, restarted, ROWS[2])

    baseline = PaperState()
    for row in ROWS:
        baseline, _ = process_bar(baseline, row)
    assert restarted == baseline
    assert replay_journal(journal) == baseline


def test_idempotent_retry_does_not_append_duplicate(tmp_path):
    journal = tmp_path / "paper.jsonl"
    state, _ = process_and_append(journal, PaperState(), ROWS[0])
    before = journal.read_bytes()
    same_state, action = process_and_append(journal, state, ROWS[0])
    assert action["status"] == "IDEMPOTENT_NOOP"
    assert same_state == state
    assert journal.read_bytes() == before


def test_same_timestamp_changed_requires_versioned_replay(tmp_path):
    journal = tmp_path / "paper.jsonl"
    state, _ = process_and_append(journal, PaperState(), ROWS[0])
    changed = dict(ROWS[0], close=999)
    with pytest.raises(ValueError, match="versioned replay required"):
        process_and_append(journal, state, changed)


def test_tampering_is_detected(tmp_path):
    journal = tmp_path / "paper.jsonl"
    process_and_append(journal, PaperState(), ROWS[0])
    record = json.loads(journal.read_text().strip())
    record["bar"]["close"] = 999
    journal.write_text(json.dumps(record) + "\n")
    with pytest.raises(JournalIntegrityError, match="record hash mismatch"):
        replay_journal(journal)


def test_stale_state_cannot_append_to_existing_journal(tmp_path):
    journal = tmp_path / "paper.jsonl"
    process_and_append(journal, PaperState(), ROWS[0])
    with pytest.raises(JournalIntegrityError, match="supplied state"):
        process_and_append(journal, PaperState(), ROWS[1])

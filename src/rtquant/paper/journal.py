from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import hashlib
import json
import os
from typing import Any

from .runner import PaperState, canonical_paper_bar, process_bar


PAPER_JOURNAL_SCHEMA_VERSION = 1


class JournalIntegrityError(RuntimeError):
    """Raised when an append-only paper journal cannot be deterministically verified."""


@dataclass(frozen=True)
class JournalCursor:
    """Verified append cursor recovered from the authoritative journal."""

    state: PaperState
    seq: int
    previous_record_hash: str | None
    file_size: int


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _record_hash(record_without_hash: dict) -> str:
    return _sha256(record_without_hash)


def _read_records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                raise JournalIntegrityError(f"blank journal line at {line_no}")
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise JournalIntegrityError(f"invalid JSON at journal line {line_no}") from exc
    return records


def recover_journal(path: str | Path) -> JournalCursor:
    """Verify the full chain once and return a cursor safe for locked appends."""
    path = Path(path)
    state = PaperState()
    previous_record_hash = None
    records = _read_records(path)
    for expected_seq, record in enumerate(records, 1):
        if record.get("schema_version") != PAPER_JOURNAL_SCHEMA_VERSION:
            raise JournalIntegrityError(
                f"unsupported journal schema at seq {expected_seq}; versioned replay required"
            )
        actual = dict(record)
        stored_record_hash = actual.pop("record_hash", None)
        if stored_record_hash is None or _record_hash(actual) != stored_record_hash:
            raise JournalIntegrityError(f"record hash mismatch at seq {expected_seq}")
        if record.get("seq") != expected_seq:
            raise JournalIntegrityError(f"sequence mismatch at seq {expected_seq}")
        if record.get("previous_record_hash") != previous_record_hash:
            raise JournalIntegrityError(f"hash-chain mismatch at seq {expected_seq}")
        if record.get("state_before_hash") != state.digest():
            raise JournalIntegrityError(f"state-before mismatch at seq {expected_seq}")

        row = record.get("bar")
        canonical_bar = canonical_paper_bar(row) if isinstance(row, dict) else None
        if canonical_bar is None or row != canonical_bar:
            raise JournalIntegrityError(f"non-canonical bar payload at seq {expected_seq}")
        if record.get("bar_hash") != _sha256(canonical_bar):
            raise JournalIntegrityError(f"bar hash mismatch at seq {expected_seq}")

        costs = record.get("execution", {})
        new_state, action = process_bar(
            state,
            canonical_bar,
            fee_bps_one_way=float(costs.get("fee_bps_one_way", 7.0)),
            slippage_bps_one_way=float(costs.get("slippage_bps_one_way", 0.0)),
        )
        if action.get("status") != "PROCESSED":
            raise JournalIntegrityError(f"journal contains non-processed duplicate at seq {expected_seq}")
        if record.get("state_after_hash") != new_state.digest():
            raise JournalIntegrityError(f"state-after hash mismatch at seq {expected_seq}")
        if record.get("state_after") != asdict(new_state):
            raise JournalIntegrityError(f"stored state mismatch at seq {expected_seq}")
        previous_record_hash = stored_record_hash
        state = new_state

    size = path.stat().st_size if path.exists() else 0
    return JournalCursor(
        state=state,
        seq=len(records),
        previous_record_hash=previous_record_hash,
        file_size=size,
    )


def replay_journal(path: str | Path) -> PaperState:
    """Verify the full hash/state chain and recover the deterministic final PaperState."""
    return recover_journal(path).state


def append_from_cursor(
    path: str | Path,
    cursor: JournalCursor,
    row: dict,
    *,
    fee_bps_one_way: float = 7.0,
    slippage_bps_one_way: float = 0.0,
):
    """Append one bar from an already verified cursor held under a single-writer lock.

    The file-size guard prevents an operational session from appending after an
    out-of-band append/truncate without first recovering and verifying the journal.
    """
    path = Path(path)
    current_size = path.stat().st_size if path.exists() else 0
    if current_size != cursor.file_size:
        raise JournalIntegrityError(
            "journal bytes changed after recovery; recover and verify before appending"
        )

    canonical_bar = canonical_paper_bar(row)
    new_state, action = process_bar(
        cursor.state,
        canonical_bar,
        fee_bps_one_way=fee_bps_one_way,
        slippage_bps_one_way=slippage_bps_one_way,
    )
    if action.get("status") == "IDEMPOTENT_NOOP":
        return cursor, action

    record = {
        "schema_version": PAPER_JOURNAL_SCHEMA_VERSION,
        "seq": cursor.seq + 1,
        "previous_record_hash": cursor.previous_record_hash,
        "bar": canonical_bar,
        "bar_hash": _sha256(canonical_bar),
        "execution": {
            "fee_bps_one_way": float(fee_bps_one_way),
            "slippage_bps_one_way": float(slippage_bps_one_way),
        },
        "state_before_hash": cursor.state.digest(),
        "state_after": asdict(new_state),
        "state_after_hash": new_state.digest(),
        "action": action,
    }
    record["record_hash"] = _record_hash(record)

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(_canonical_json(record) + "\n")
        f.flush()
        os.fsync(f.fileno())

    return JournalCursor(
        state=new_state,
        seq=cursor.seq + 1,
        previous_record_hash=record["record_hash"],
        file_size=path.stat().st_size,
    ), action


def process_and_append(
    path: str | Path,
    state: PaperState,
    row: dict,
    *,
    fee_bps_one_way: float = 7.0,
    slippage_bps_one_way: float = 0.0,
):
    """Compatibility wrapper: fully recover, verify supplied state, then append."""
    cursor = recover_journal(path)
    if cursor.state != state:
        raise JournalIntegrityError("supplied state does not match journal-recovered state")
    new_cursor, action = append_from_cursor(
        path,
        cursor,
        row,
        fee_bps_one_way=fee_bps_one_way,
        slippage_bps_one_way=slippage_bps_one_way,
    )
    return new_cursor.state, action

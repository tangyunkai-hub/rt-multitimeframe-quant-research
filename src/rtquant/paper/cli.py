from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Iterable

import pandas as pd

from .journal import recover_journal
from .session import PaperSession


REQUIRED_INPUT_FIELDS = ("timestamp", "open", "close", "target_exposure")
PERFORMANCE_EMBARGO_ACTIVE = True


def _json_print(payload: dict) -> None:
    print(json.dumps(payload, sort_keys=True, indent=2, default=str))


def _validate_row(row: dict) -> dict:
    missing = [field for field in REQUIRED_INPUT_FIELDS if field not in row]
    if missing:
        raise ValueError(f"missing required paper input fields: {missing}")

    ts = pd.Timestamp(row["timestamp"])
    if pd.isna(ts):
        raise ValueError("timestamp must be valid")

    normalized = dict(row)
    for field in ("open", "close", "target_exposure"):
        value = float(row[field])
        if not math.isfinite(value):
            raise ValueError(f"{field} must be finite")
        normalized[field] = value
    if normalized["open"] <= 0 or normalized["close"] <= 0:
        raise ValueError("open and close must be positive")
    normalized["timestamp"] = row["timestamp"]
    return normalized


def load_rows(path: str | Path) -> list[dict]:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        frame = pd.read_csv(path)
        rows = frame.to_dict(orient="records")
    elif suffix in {".jsonl", ".ndjson"}:
        rows = []
        with path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, 1):
                line = line.strip()
                if not line:
                    raise ValueError(f"blank JSONL line at {line_no}")
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError(f"JSONL line {line_no} must be an object")
                rows.append(value)
    else:
        raise ValueError("paper input must be .csv, .jsonl, or .ndjson")

    if not rows:
        raise ValueError("paper input contains no rows")
    return [_validate_row(dict(row)) for row in rows]


def redacted_health(health: dict) -> dict:
    """Allowlist operational fields; never surface performance during embargo."""
    allowed = (
        "status",
        "session_id",
        "journal_seq",
        "journal_tail_hash",
        "journal_file_size",
        "last_timestamp",
        "state_hash",
        "held_exposure",
        "pending_target",
        "processed_this_session",
        "idempotent_retries_this_session",
        "broker_route",
    )
    payload = {key: health.get(key) for key in allowed if key in health}
    payload["performance_embargo_active"] = PERFORMANCE_EMBARGO_ACTIVE
    payload["performance_fields_released"] = False
    payload["broker_route"] = False
    return payload


def _redacted_action(action: dict) -> dict:
    allowed = ("status", "timestamp", "state_hash")
    return {key: action.get(key) for key in allowed if key in action}


def ingest_path(
    *,
    journal_path: str | Path,
    input_path: str | Path,
    fee_bps_one_way: float = 7.0,
    slippage_bps_one_way: float = 0.0,
    recover_stale_lock: bool = False,
) -> dict:
    rows = load_rows(input_path)
    with PaperSession(
        journal_path,
        fee_bps_one_way=fee_bps_one_way,
        slippage_bps_one_way=slippage_bps_one_way,
        recover_stale_lock=recover_stale_lock,
    ) as session:
        actions = session.ingest_many(rows)
        health = redacted_health(session.health())

    processed = sum(action.get("status") == "PROCESSED" for action in actions)
    idempotent = sum(action.get("status") == "IDEMPOTENT_NOOP" for action in actions)
    return {
        "status": "OK",
        "mode": "BROKERLESS_PAPER_ONLY",
        "broker_route": False,
        "performance_embargo_active": PERFORMANCE_EMBARGO_ACTIVE,
        "performance_fields_released": False,
        "input_rows": len(rows),
        "processed_rows": processed,
        "idempotent_rows": idempotent,
        "actions": [_redacted_action(action) for action in actions],
        "health": health,
    }


def status_payload(journal_path: str | Path) -> dict:
    journal = Path(journal_path)
    lock_path = journal.with_suffix(journal.suffix + ".lock")
    if lock_path.exists():
        # Do not race an active writer. The operational session itself owns the
        # authoritative cursor while the lock is present.
        return {
            "status": "ACTIVE_WRITER_LOCK_PRESENT",
            "mode": "BROKERLESS_PAPER_ONLY",
            "journal": str(journal),
            "broker_route": False,
            "performance_embargo_active": PERFORMANCE_EMBARGO_ACTIVE,
            "performance_fields_released": False,
        }

    cursor = recover_journal(journal)
    return {
        "status": "VERIFIED_IDLE",
        "mode": "BROKERLESS_PAPER_ONLY",
        "journal": str(journal),
        "journal_seq": cursor.seq,
        "journal_tail_hash": cursor.previous_record_hash,
        "journal_file_size": cursor.file_size,
        "last_timestamp": cursor.state.last_timestamp,
        "state_hash": cursor.state.digest(),
        "held_exposure": cursor.state.held_exposure,
        "pending_target": cursor.state.pending_target,
        "broker_route": False,
        "performance_embargo_active": PERFORMANCE_EMBARGO_ACTIVE,
        "performance_fields_released": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rtquant-paper",
        description=(
            "Brokerless paper-operation CLI. It never routes live orders and "
            "does not release performance fields while the prospective embargo is active."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest = subparsers.add_parser("ingest", help="append validated paper bars to a journal")
    ingest.add_argument("--journal", required=True)
    ingest.add_argument("--input", required=True)
    ingest.add_argument("--fee-bps-one-way", type=float, default=7.0)
    ingest.add_argument("--slippage-bps-one-way", type=float, default=0.0)
    ingest.add_argument(
        "--recover-stale-lock",
        action="store_true",
        help="explicitly recover a stale same-host writer lock after PID liveness check",
    )

    status = subparsers.add_parser("status", help="verify an idle journal and show redacted health")
    status.add_argument("--journal", required=True)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        if args.command == "ingest":
            payload = ingest_path(
                journal_path=args.journal,
                input_path=args.input,
                fee_bps_one_way=args.fee_bps_one_way,
                slippage_bps_one_way=args.slippage_bps_one_way,
                recover_stale_lock=args.recover_stale_lock,
            )
        else:
            payload = status_payload(args.journal)
    except Exception as exc:
        _json_print({
            "status": "ERROR",
            "error_type": type(exc).__name__,
            "message": str(exc),
            "mode": "BROKERLESS_PAPER_ONLY",
            "broker_route": False,
            "performance_embargo_active": PERFORMANCE_EMBARGO_ACTIVE,
            "performance_fields_released": False,
        })
        return 2

    _json_print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

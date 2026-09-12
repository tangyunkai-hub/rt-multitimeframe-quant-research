from __future__ import annotations

from contextlib import AbstractContextManager
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import socket
import uuid

from .journal import JournalCursor, append_from_cursor, recover_journal


class SessionLockError(RuntimeError):
    """Raised when a brokerless paper journal already has an active writer."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


class PaperSession(AbstractContextManager):
    """Single-writer, restart-safe brokerless paper operation.

    The hash-chained journal remains the only authoritative state.  The checkpoint
    is a disposable operational cache written atomically after successful appends.
    No broker or order-routing functionality exists here.
    """

    def __init__(
        self,
        journal_path: str | Path,
        *,
        fee_bps_one_way: float = 7.0,
        slippage_bps_one_way: float = 0.0,
        recover_stale_lock: bool = False,
    ):
        self.journal_path = Path(journal_path)
        self.lock_path = self.journal_path.with_suffix(self.journal_path.suffix + ".lock")
        self.checkpoint_path = self.journal_path.with_suffix(
            self.journal_path.suffix + ".checkpoint.json"
        )
        self.sessions_path = self.journal_path.with_suffix(
            self.journal_path.suffix + ".sessions.jsonl"
        )
        self.fee_bps_one_way = float(fee_bps_one_way)
        self.slippage_bps_one_way = float(slippage_bps_one_way)
        self.recover_stale_lock = bool(recover_stale_lock)
        self.session_id = str(uuid.uuid4())
        self.hostname = socket.gethostname()
        self.pid = os.getpid()
        self._lock_token = str(uuid.uuid4())
        self._cursor: JournalCursor | None = None
        self._entered = False
        self._processed = 0
        self._idempotent = 0

    @property
    def cursor(self) -> JournalCursor:
        if not self._entered or self._cursor is None:
            raise RuntimeError("paper session is not active")
        return self._cursor

    @property
    def state(self):
        return self.cursor.state

    def _read_lock(self) -> dict | None:
        try:
            return json.loads(self.lock_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None
        except (OSError, json.JSONDecodeError):
            return {"unreadable": True}

    def _can_recover_existing_lock(self, owner: dict | None) -> bool:
        if not self.recover_stale_lock or not isinstance(owner, dict):
            return False
        if owner.get("unreadable"):
            return False
        if owner.get("hostname") != self.hostname:
            return False
        try:
            owner_pid = int(owner.get("pid"))
        except (TypeError, ValueError):
            return False
        return not _pid_alive(owner_pid)

    def _acquire_lock(self) -> None:
        self.journal_path.parent.mkdir(parents=True, exist_ok=True)
        lock_payload = {
            "schema_version": 1,
            "session_id": self.session_id,
            "token": self._lock_token,
            "pid": self.pid,
            "hostname": self.hostname,
            "journal": self.journal_path.name,
            "acquired_at_utc": _utc_now_iso(),
        }
        payload = (_canonical_json(lock_payload) + "\n").encode("utf-8")

        for attempt in range(2):
            try:
                fd = os.open(
                    self.lock_path,
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                    0o600,
                )
            except FileExistsError:
                owner = self._read_lock()
                if attempt == 0 and self._can_recover_existing_lock(owner):
                    try:
                        self.lock_path.unlink()
                    except FileNotFoundError:
                        pass
                    continue
                raise SessionLockError(
                    f"paper journal already has a writer lock: {owner}"
                )
            else:
                try:
                    os.write(fd, payload)
                    os.fsync(fd)
                finally:
                    os.close(fd)
                return
        raise SessionLockError("could not acquire paper journal writer lock")

    def _release_lock(self) -> None:
        owner = self._read_lock()
        if not isinstance(owner, dict) or owner.get("token") != self._lock_token:
            raise SessionLockError("writer lock ownership changed; refusing to remove lock")
        try:
            self.lock_path.unlink()
        except FileNotFoundError as exc:
            raise SessionLockError("writer lock disappeared before release") from exc

    def _append_session_event(self, event: str, **extra) -> None:
        payload = {
            "schema_version": 1,
            "session_id": self.session_id,
            "event": event,
            "timestamp_utc": _utc_now_iso(),
            "pid": self.pid,
            "hostname": self.hostname,
            "journal_seq": self.cursor.seq if self._cursor is not None else None,
            **extra,
        }
        self.sessions_path.parent.mkdir(parents=True, exist_ok=True)
        with self.sessions_path.open("a", encoding="utf-8", newline="\n") as f:
            f.write(_canonical_json(payload) + "\n")
            f.flush()
            os.fsync(f.fileno())

    def _checkpoint_payload(self) -> dict:
        c = self.cursor
        return {
            "schema_version": 1,
            "authoritative": False,
            "authority_note": "cache only; recover and verify the hash-chained journal on restart",
            "session_id": self.session_id,
            "updated_at_utc": _utc_now_iso(),
            "journal": self.journal_path.name,
            "journal_seq": c.seq,
            "journal_tail_hash": c.previous_record_hash,
            "journal_file_size": c.file_size,
            "state_hash": c.state.digest(),
            "last_timestamp": c.state.last_timestamp,
            "held_exposure": c.state.held_exposure,
            "pending_target": c.state.pending_target,
            "equity": c.state.equity,
        }

    def _write_checkpoint(self) -> None:
        payload = _canonical_json(self._checkpoint_payload()) + "\n"
        tmp = self.checkpoint_path.with_suffix(
            self.checkpoint_path.suffix + f".{self.session_id}.tmp"
        )
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        with tmp.open("w", encoding="utf-8", newline="\n") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, self.checkpoint_path)

    def __enter__(self):
        if self._entered:
            raise RuntimeError("paper session cannot be entered twice")
        self._acquire_lock()
        try:
            self._cursor = recover_journal(self.journal_path)
            self._entered = True
            self._write_checkpoint()
            self._append_session_event(
                "STARTED",
                recovered_existing_journal=self.cursor.seq > 0,
                fee_bps_one_way=self.fee_bps_one_way,
                slippage_bps_one_way=self.slippage_bps_one_way,
            )
            return self
        except Exception:
            try:
                self._release_lock()
            finally:
                self._entered = False
                self._cursor = None
            raise

    def ingest(self, row: dict) -> dict:
        if not self._entered:
            raise RuntimeError("paper session is not active")
        new_cursor, action = append_from_cursor(
            self.journal_path,
            self.cursor,
            row,
            fee_bps_one_way=self.fee_bps_one_way,
            slippage_bps_one_way=self.slippage_bps_one_way,
        )
        self._cursor = new_cursor
        if action.get("status") == "PROCESSED":
            self._processed += 1
            self._write_checkpoint()
        else:
            self._idempotent += 1
        return action

    def ingest_many(self, rows) -> list[dict]:
        return [self.ingest(dict(row)) for row in rows]

    def health(self) -> dict:
        c = self.cursor
        return {
            "status": "ACTIVE",
            "session_id": self.session_id,
            "journal_seq": c.seq,
            "journal_tail_hash": c.previous_record_hash,
            "journal_file_size": c.file_size,
            "last_timestamp": c.state.last_timestamp,
            "state_hash": c.state.digest(),
            "equity": c.state.equity,
            "held_exposure": c.state.held_exposure,
            "pending_target": c.state.pending_target,
            "processed_this_session": self._processed,
            "idempotent_retries_this_session": self._idempotent,
            "broker_route": False,
        }

    def __exit__(self, exc_type, exc, tb):
        if not self._entered:
            return False
        release_error = None
        try:
            self._write_checkpoint()
            self._append_session_event(
                "FAILED" if exc_type else "STOPPED",
                processed_this_session=self._processed,
                idempotent_retries_this_session=self._idempotent,
                error_type=exc_type.__name__ if exc_type else None,
            )
        finally:
            try:
                self._release_lock()
            except Exception as lock_exc:
                release_error = lock_exc
            self._entered = False
            self._cursor = None
        if release_error is not None and exc_type is None:
            raise release_error
        return False

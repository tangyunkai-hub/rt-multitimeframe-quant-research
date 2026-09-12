from dataclasses import dataclass, asdict
import hashlib, json
import pandas as pd


def _hash(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True, default=str).encode()).hexdigest()


def canonical_paper_bar(row: dict) -> dict:
    """Normalize equivalent bar representations before identity hashing.

    Timestamps are canonicalized to UTC and numeric execution/state fields to float,
    so representation-only differences (for example Z vs +00:00 or 100 vs 100.0)
    do not create a false historical-correction event.
    """
    ts = pd.Timestamp(row["timestamp"])
    ts = ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")
    return {
        "timestamp": ts.isoformat(),
        "open": float(row["open"]),
        "close": float(row["close"]),
        "target_exposure": float(row["target_exposure"]),
    }


@dataclass
class PaperState:
    last_timestamp: str | None = None
    last_bar_hash: str | None = None
    held_exposure: float = 0.0
    pending_target: float | None = None
    equity: float = 1.0
    last_close: float | None = None

    def digest(self):
        return _hash(asdict(self))


def process_bar(
    state: PaperState,
    row: dict,
    *,
    fee_bps_one_way=7.0,
    slippage_bps_one_way=0.0,
):
    bar = canonical_paper_bar(row)
    ts = pd.Timestamp(bar["timestamp"])
    bh = _hash(bar)
    if state.last_timestamp:
        last = pd.Timestamp(state.last_timestamp)
        if ts < last:
            raise ValueError("non-monotonic timestamp")
        if ts == last:
            if bh == state.last_bar_hash:
                return state, {"status": "IDEMPOTENT_NOOP"}
            raise ValueError("same timestamp changed: versioned replay required")

    op = bar["open"]
    cl = bar["close"]
    old = state.held_exposure
    target = old if state.pending_target is None else float(state.pending_target)
    eq = state.equity
    if state.last_close is not None:
        eq *= 1 + old * (op / state.last_close - 1)
    turn = abs(target - old)
    eq *= 1 - turn * (fee_bps_one_way + slippage_bps_one_way) / 10000.0
    eq *= 1 + target * (cl / op - 1)
    ns = PaperState(
        bar["timestamp"],
        bh,
        target,
        bar["target_exposure"],
        eq,
        cl,
    )
    return ns, {
        "status": "PROCESSED",
        "timestamp": bar["timestamp"],
        "turnover": turn,
        "equity": eq,
        "state_hash": ns.digest(),
    }

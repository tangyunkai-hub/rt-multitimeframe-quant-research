from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

import pandas as pd

BASE = "https://www.bitstamp.net/api/v2/ohlc"
STEPS = {"12h": 43200, "1d": 86400}
FREEZE = pd.Timestamp("2026-09-12T02:00:00Z")
FULL_SCOPE = "FULL_REBUILD_COMPLETE_FORWARD_POOL"
MONITOR_SCOPE = "MONITOR_BOUNDED_OVERLAP_NOT_COMPLETE_FORWARD_POOL"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "rtquant-forward-bitstamp-state/1.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()


def collect_raw(market: str, step: int, start_open: int, end_open: int,
                loader: Callable[[str], bytes] = get):
    rows: dict[int, dict] = {}
    requests = []
    cursor = end_open
    while cursor >= start_open:
        q = urllib.parse.urlencode({
            "step": step, "limit": 1000, "end": cursor,
            "exclude_current_candle": "true",
        })
        url = f"{BASE}/{market}/?{q}"
        blob = loader(url)
        js = json.loads(blob.decode("utf-8"))
        batch = js.get("data", {}).get("ohlc", [])
        requests.append({
            "market": market, "step": step, "request_end_epoch": cursor,
            "url": url, "payload_sha256": sha256_bytes(blob), "rows": len(batch),
        })
        if not batch:
            break
        ts = [int(r["timestamp"]) for r in batch]
        for row in batch:
            t = int(row["timestamp"])
            if start_open <= t <= end_open:
                rows[t] = row
        earliest = min(ts)
        if earliest <= start_open:
            break
        nxt = earliest - step
        if nxt >= cursor:
            raise RuntimeError("Bitstamp pagination did not progress")
        cursor = nxt
        time.sleep(0.02)

    data = []
    for t in sorted(rows):
        r = rows[t]
        data.append({
            "open_time": pd.to_datetime(t, unit="s", utc=True),
            "availability_time": pd.to_datetime(t + step, unit="s", utc=True),
            "open": float(r["open"]), "high": float(r["high"]),
            "low": float(r["low"]), "close": float(r["close"]),
            "volume": float(r["volume"]),
        })
    return pd.DataFrame(data), requests


def default_end_date() -> date:
    return datetime.now(timezone.utc).date() - timedelta(days=1)


def collect_forward_state(*, out: Path, end_day: date, mode: str,
                          raw_collector: Callable = collect_raw) -> dict:
    if mode not in {"monitor", "full"}:
        raise ValueError(f"unsupported mode: {mode}")
    out = Path(out)
    state_dir = out / "bitstamp"
    state_dir.mkdir(parents=True, exist_ok=True)
    cutoff = pd.Timestamp(end_day, tz="UTC") + pd.Timedelta(days=1)
    if cutoff <= FREEZE:
        gate = {
            "status": "WAITING_NO_COMPLETED_POST_FREEZE_UTC_DAY",
            "classification": "POST_FREEZE_BITSTAMP_STATE_ONLY_DATA",
            "mode": mode,
            "data_scope": FULL_SCOPE if mode == "full" else MONITOR_SCOPE,
            "freeze_boundary_utc_exclusive": FREEZE.isoformat(),
            "availability_cutoff_utc_inclusive": cutoff.isoformat(),
            "performance_evaluation_allowed": False,
            "candidate_b_judgement_allowed": False,
            "price_pnl_use_allowed": False,
            "state_only": True,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        (state_dir / "DATA_GATE.json").write_text(json.dumps(gate, indent=2), encoding="utf-8")
        return gate

    audits = []
    manifest = []
    waiting = []
    for label, step in STEPS.items():
        overlap_start = FREEZE - pd.Timedelta(seconds=step)
        if mode == "monitor":
            overlap_start = max(overlap_start, cutoff - pd.Timedelta(days=4))
        start_open = int(overlap_start.timestamp())
        end_open = int((cutoff - pd.Timedelta(seconds=step)).timestamp())
        d, reqs = raw_collector("btcusd", step, start_open, end_open)
        manifest.extend(reqs)
        if d.empty:
            eligible = d
        else:
            d["availability_time"] = pd.to_datetime(d["availability_time"], utc=True)
            eligible = d[(d.availability_time > FREEZE) & (d.availability_time <= cutoff)].copy()
        path = state_dir / f"BTCUSD_{label}_forward.csv.gz"
        eligible.to_csv(path, index=False, compression="gzip")

        if len(eligible):
            dup = int(eligible.availability_time.duplicated().sum())
            mono = bool(eligible.availability_time.is_monotonic_increasing)
            env = ((eligible.high < eligible[["open", "close", "low"]].max(axis=1)) |
                   (eligible.low > eligible[["open", "close", "high"]].min(axis=1)))
            nonpos = (eligible[["open", "high", "low", "close"]] <= 0).any(axis=1)
            out_of_range = ((eligible.availability_time <= FREEZE) |
                            (eligible.availability_time > cutoff))
            status = "PASS" if not (dup or not mono or env.any() or nonpos.any() or out_of_range.any()) else "FAIL"
        else:
            dup = 0; mono = True
            env = pd.Series(dtype=bool); nonpos = pd.Series(dtype=bool); out_of_range = pd.Series(dtype=bool)
            status = "WAITING_FIRST_COMPLETED_STATE_BAR"
            waiting.append(label)

        audits.append({
            "interval": label, "rows": int(len(eligible)),
            "eligible_start_availability": str(eligible.availability_time.iloc[0]) if len(eligible) else None,
            "eligible_end_availability": str(eligible.availability_time.iloc[-1]) if len(eligible) else None,
            "duplicate_timestamps": dup, "monotonic": mono,
            "ohlc_envelope_failures": int(env.sum()) if len(env) else 0,
            "nonpositive_price_rows": int(nonpos.sum()) if len(nonpos) else 0,
            "availability_out_of_range": int(out_of_range.sum()) if len(out_of_range) else 0,
            "sha256": sha256_bytes(path.read_bytes()), "status": status,
        })

    audit = pd.DataFrame(audits)
    audit.to_csv(state_dir / "integrity.csv", index=False)
    pd.DataFrame(manifest).to_csv(state_dir / "request_manifest.csv", index=False)
    hard = audit[audit.status == "FAIL"] if len(audit) else audit
    overall = "FAIL" if len(hard) else ("WAITING_FIRST_COMPLETED_STATE_BAR" if waiting else "PASS")
    gate = {
        "status": overall,
        "classification": "POST_FREEZE_BITSTAMP_STATE_ONLY_DATA",
        "mode": mode,
        "data_scope": FULL_SCOPE if mode == "full" else MONITOR_SCOPE,
        "freeze_boundary_utc_exclusive": FREEZE.isoformat(),
        "availability_cutoff_utc_inclusive": cutoff.isoformat(),
        "intervals": list(STEPS),
        "waiting_series": waiting,
        "performance_evaluation_allowed": Falsl
        "candidate_b_judgement_allowed": False,
        "price_pnl_use_allowed": Falsl
        "state_only": True,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (state_dir / "DATA_GATE.json").write_text(json.dumps(gate, indent=2), encoding="utf-8")
    if overall == "FAIL":
        raise SystemExit("Bitstamp forward state-only integrity gate failed")
    return gate


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="forward_native_data")
    ap.add_argument("--end-date", default=None)
    ap.add_argument("--mode", choices=("monitor", "full"), default="monitor")
    args = ap.parse_args()
    end_day = date.fromisoformat(args.end_date) if args.end_date else default_end_date()
    gate = collect_forward_state(out=Path(args.out), end_day=end_day, mode=args.mode)
    print(json.dumps(gate, indent=2))


if __name__ == "__main__":
    main()

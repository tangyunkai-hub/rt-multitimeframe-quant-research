from __future__ import annotations

import argparse
import hashlib
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import pandas as pd
import requests

BASE = "https://api.exchange.coinbase.com"
GRANULARITY_SECONDS = 900
MAX_CANDLES_PER_REQUEST = 299
USER_AGENT = "rt-multitimeframe-quant-research/coinbase-cross-exchange-audit"


@dataclass
class IntegrityRow:
    product: str
    rows: int
    first_open_time: str | None
    last_open_time: str | None
    duplicate_timestamps: int
    monotonic: bool
    ohlc_envelope_failures: int
    nonpositive_price_rows: int
    timestamp_out_of_range: int
    gap_events: int
    missing_15m_intervals: int
    sha256_normalized_csv_gz: str
    status: str


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def utc_iso(ts: pd.Timestamp) -> str:
    return ts.tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")


def request_candles(session: requests.Session, product: str, start: pd.Timestamp, end: pd.Timestamp) -> tuple[list[Any], int]:
    url = f"{BASE}/products/{product}/candles"
    params = {
        "granularity": GRANULARITY_SECONDS,
        "start": utc_iso(start),
        "end": utc_iso(end),
    }
    last_exc: Exception | None = None
    for attempt in range(6):
        try:
            r = session.get(url, params=params, timeout=30)
            if r.status_code == 429:
                time.sleep(min(10.0, 0.75 * (2**attempt)))
                continue
            r.raise_for_status()
            payload = r.json()
            if not isinstance(payload, list):
                raise RuntimeError(f"unexpected Coinbase payload type: {type(payload)!r}")
            return payload, r.status_code
        except Exception as exc:
            last_exc = exc
            if attempt == 5:
                raise
            time.sleep(min(10.0, 0.75 * (2**attempt)))
    raise RuntimeError(f"unreachable request failure: {last_exc}")


def download_product(product: str, start: pd.Timestamp, end: pd.Timestamp, out_dir: Path, sleep_seconds: float) -> tuple[Path, dict[str, Any]]:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
    rows: list[list[Any]] = []
    reqs = 0
    status_counts: dict[str, int] = {}
    cursor = start
    span = pd.Timedelta(seconds=GRANULARITY_SECONDS * MAX_CANDLES_PER_REQUEST)

    while cursor < end:
        chunk_end = min(end, cursor + span)
        payload, status = request_candles(session, product, cursor, chunk_end)
        reqs += 1
        status_counts[str(status)] = status_counts.get(str(status), 0) + 1
        rows.extend(payload)
        cursor = chunk_end
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)

    # Coinbase candle schema: [time, low, high, open, close, volume].
    df = pd.DataFrame(rows, columns=["epoch_s", "low", "high", "open", "close", "volume"])
    if df.empty:
        raise RuntimeError(f"no candles returned for {product}")

    for c in ["epoch_s", "low", "high", "open", "close", "volume"]:
        df[c] = pd.to_numeric(df[c], errors="raise")
    df["open_time"] = pd.to_datetime(df["epoch_s"].astype("int64"), unit="s", utc=True)
    raw_out_of_range = int(((df.open_time < start) | (df.open_time >= end)).sum())
    df = df[(df.open_time >= start) & (df.open_time < end)].copy()
    df = df.sort_values("open_time").drop_duplicates("open_time", keep="last").reset_index(drop=True)
    df["availability_time"] = df["open_time"] + pd.Timedelta(minutes=15)
    df = df[["open_time", "availability_time", "open", "high", "low", "close", "volume"]]

    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{product.replace('-', '')}_15m_2017-2022.csv.gz"
    df.to_csv(path, index=False, compression="gzip")

    dup = int(df.open_time.duplicated().sum())
    monotonic = bool(df.open_time.is_monotonic_increasing)
    ohlc_fail = int(((df.high < df[["open", "close"]].max(axis=1)) | (df.low > df[["open", "close"]].min(axis=1)) | (df.high < df.low)).sum())
    nonpos = int((df[["open", "high", "low", "close"]] <= 0).any(axis=1).sum())
    out_of_range = int(((df.open_time < start) | (df.open_time >= end)).sum())
    delta = df.open_time.diff().dropna()
    gap_mask = delta > pd.Timedelta(minutes=15)
    gap_events = int(gap_mask.sum())
    missing = int(sum(max(0, int(d / pd.Timedelta(minutes=15)) - 1) for d in delta[gap_mask]))
    status_ok = dup == 0 and monotonic and ohlc_fail == 0 and nonpos == 0 and out_of_range == 0

    meta = {
        "product": product,
        "requests": reqs,
        "http_status_counts": status_counts,
        "raw_rows_received": len(rows),
        "raw_rows_outside_requested_window_before_filter": raw_out_of_range,
        "normalized_rows": int(len(df)),
        "requested_start": str(start),
        "requested_end_exclusive": str(end),
    }
    integ = IntegrityRow(
        product=product,
        rows=int(len(df)),
        first_open_time=str(df.open_time.min()) if len(df) else None,
        last_open_time=str(df.open_time.max()) if len(df) else None,
        duplicate_timestamps=dup,
        monotonic=monotonic,
        ohlc_envelope_failures=ohlc_fail,
        nonpositive_price_rows=nonpos,
        timestamp_out_of_range=out_of_range,
        gap_events=gap_events,
        missing_15m_intervals=missing,
        sha256_normalized_csv_gz=sha256(path),
        status="PASS" if status_ok else "FAIL",
    )
    return path, {"request": meta, "integrity": asdict(integ)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="cross_exchange_coinbase")
    ap.add_argument("--start", default="2017-08-17T00:00:00Z")
    ap.add_argument("--end", default="2023-01-01T00:00:00Z")
    ap.add_argument("--sleep-seconds", type=float, default=0.12)
    args = ap.parse_args()

    start = pd.Timestamp(args.start)
    end = pd.Timestamp(args.end)
    if start.tzinfo is None or end.tzinfo is None or end <= start:
        raise ValueError("start/end must be timezone-aware and end > start")

    out = Path(args.out_dir)
    results = []
    for product in ["BTC-USD", "ETH-USD"]:
        path, info = download_product(product, start, end, out / "coinbase", args.sleep_seconds)
        info["normalized_path"] = str(path)
        results.append(info)

    integrity = pd.DataFrame([r["integrity"] for r in results])
    integrity.to_csv(out / "coinbase_integrity.csv", index=False)
    (out / "coinbase_request_manifest.json").write_text(json.dumps([r["request"] for r in results], indent=2), encoding="utf-8")
    gate = {
        "classification": "CROSS_EXCHANGE_EXECUTION_ROBUSTNESS_NOT_PROSPECTIVE",
        "purpose": "DATA_ONLY_NO_STRATEGY_PERFORMANCE",
        "provider": "Coinbase Exchange public candles",
        "granularity_seconds": GRANULARITY_SECONDS,
        "requested_start": str(start),
        "requested_end_exclusive": str(end),
        "failed_series": int((integrity.status != "PASS").sum()),
        "status": "PASS" if (integrity.status == "PASS").all() else "FAIL",
        "performance_evaluation_allowed": False,
        "protocol": "research/cross_exchange_execution_prereg_2026-09-12.md",
    }
    (out / "DATA_GATE.json").write_text(json.dumps(gate, indent=2), encoding="utf-8")
    print(integrity.to_string(index=False))
    print(json.dumps(gate, indent=2))
    if gate["status"] != "PASS":
        raise SystemExit("Coinbase cross-exchange data integrity gate failed")


if __name__ == "__main__":
    main()

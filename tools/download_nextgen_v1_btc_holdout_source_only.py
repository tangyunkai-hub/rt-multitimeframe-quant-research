from __future__ import annotations

import gzip
import hashlib
import io
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

BITFINEX_BASE = "https://api-pub.bitfinex.com/v2/candles"
SYMBOL = "tBTCUSD"
START = pd.Timestamp("2017-08-17T00:00:00Z")
END = pd.Timestamp("2026-09-01T00:00:00Z")
STEP = pd.Timedelta(minutes=15)
OUT = Path("nextgen_v1_btc_holdout_source")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def get(url: str, retries: int = 6) -> bytes:
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "rtquant-nextgen-holdout-source/1.0"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read()
        except Exception as e:
            last = e
            time.sleep(min(2 ** i, 15))
    raise RuntimeError(f"download failed {url}: {last}")


def audit(df: pd.DataFrame) -> dict:
    t = pd.to_datetime(df["open_time"], utc=True)
    diffs = t.diff().dropna()
    gaps = diffs[diffs != STEP]
    env = (
        (df["high"] < df[["open", "close", "low"]].max(axis=1)) |
        (df["low"] > df[["open", "close", "high"]].min(axis=1))
    )
    return {
        "rows": int(len(df)),
        "start": str(t.iloc[0]) if len(t) else None,
        "end": str(t.iloc[-1]) if len(t) else None,
        "duplicates": int(t.duplicated().sum()),
        "monotonic": bool(t.is_monotonic_increasing),
        "ohlc_envelope_failures": int(env.sum()),
        "gap_events": int(len(gaps)),
        "missing_15m_intervals_estimate": int(sum(max(int(d / STEP) - 1, 0) for d in gaps)),
        "max_gap_seconds": float(gaps.max().total_seconds()) if len(gaps) else 0.0,
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    start_ms = int(START.timestamp() * 1000)
    end_ms = int((END - pd.Timedelta(milliseconds=1)).timestamp() * 1000)
    cursor = start_ms
    rows: dict[int, list] = {}
    manifest = []

    while cursor <= end_ms:
        q = urllib.parse.urlencode({"start": cursor, "end": end_ms, "limit": 10000, "sort": 1})
        url = f"{BITFINEX_BASE}/trade:15m:{SYMBOL}/hist?{q}"
        blob = get(url)
        batch = json.loads(blob.decode("utf-8"))
        manifest.append({
            "source": "Bitfinex",
            "instrument": SYMBOL,
            "url": url,
            "payload_sha256": sha256_bytes(blob),
            "rows": len(batch),
        })
        if not batch:
            break
        for r in batch:
            rows[int(r[0])] = r
        last = max(int(r[0]) for r in batch)
        if last >= end_ms or len(batch) < 10000:
            break
        nxt = last + 1
        if nxt <= cursor:
            raise RuntimeError("Bitfinex pagination stalled")
        cursor = nxt
        time.sleep(0.20)

    if not rows:
        raise RuntimeError("no Bitfinex holdout candles acquired")

    recs = []
    for mts in sorted(rows):
        r = rows[mts]
        recs.append({
            "open_time": pd.to_datetime(mts, unit="ms", utc=True),
            "availability_time": pd.to_datetime(mts, unit="ms", utc=True) + STEP,
            "open": float(r[1]),
            "high": float(r[3]),
            "low": float(r[4]),
            "close": float(r[2]),
            "volume": float(r[5]),
        })
    df = pd.DataFrame(recs)
    df = df[(df.open_time >= START) & (df.open_time < END)].sort_values("open_time").drop_duplicates("open_time", keep="last").reset_index(drop=True)

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    csv_sha = sha256_bytes(csv_bytes)
    csv_path = OUT / "tBTCUSD_15m_2017-08-17_2026-08-31.csv"
    csv_path.write_bytes(csv_bytes)
    gz_path = OUT / "tBTCUSD_15m_2017-08-17_2026-08-31.csv.gz"
    with open(gz_path, "wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as z:
            z.write(csv_bytes)
    gz_sha = sha256_bytes(gz_path.read_bytes())

    ad = audit(df)
    availability_ok = bool((pd.to_datetime(df.availability_time, utc=True) == pd.to_datetime(df.open_time, utc=True) + STEP).all())
    hard_pass = bool(
        ad["rows"] > 0 and ad["duplicates"] == 0 and ad["monotonic"] and
        ad["ohlc_envelope_failures"] == 0 and availability_ok and
        pd.Timestamp(ad["start"]) >= START and pd.Timestamp(ad["end"]) < END
    )
    ad.update({
        "source": "Bitfinex",
        "instrument": SYMBOL,
        "requested_start_inclusive": START.isoformat(),
        "requested_end_exclusive": END.isoformat(),
        "availability_identity_open_plus_15m": availability_ok,
        "decompressed_csv_sha256": csv_sha,
        "deterministic_gzip_sha256": gz_sha,
        "source_file": str(gz_path),
    })
    pd.DataFrame(manifest).to_csv(OUT / "source_request_manifest.csv", index=False)
    pd.DataFrame([ad]).to_csv(OUT / "source_integrity_audit.csv", index=False)

    gate = {
        "status": "PASS_SOURCE_ONLY" if hard_pass else "FAIL_SOURCE_ONLY",
        "classification": "NEXTGEN_V1_BTC_CROSS_VENUE_HOLDOUT_SOURCE_ONLY__PERFORMANCE_EMBARGOED",
        "source": "Bitfinex",
        "instrument": SYMBOL,
        "start_inclusive": START.isoformat(),
        "end_exclusive": END.isoformat(),
        "decompressed_csv_sha256": csv_sha,
        "deterministic_gzip_sha256": gz_sha,
        "gap_policy": "PRESERVE_NATIVE_GAPS_NO_SYNTHETIC_FILL",
        "nextgen_signal_generation_allowed": False,
        "nextgen_event_count_read_allowed": False,
        "nextgen_trade_simulation_allowed": False,
        "nextgen_performance_read_allowed": False,
        "candidate_must_be_frozen_before_holdout_use": True,
        "validated_alpha": "NO",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (OUT / "SOURCE_GATE.json").write_text(json.dumps(gate, indent=2), encoding="utf-8")
    print(json.dumps(gate, indent=2))
    print(pd.DataFrame([ad]).to_string(index=False))
    if not hard_pass:
        raise SystemExit("holdout source-only integrity gate failed")


if __name__ == "__main__":
    main()

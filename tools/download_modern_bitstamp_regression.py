from __future__ import annotations

import argparse, hashlib, json, time, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

BASE = "https://www.bitstamp.net/api/v2/ohlc"
STEPS = {"12h": 43200, "1d": 86400}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "rtquant-bitstamp-regression/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def collect(market: str, step: int, start: int, end: int):
    rows = {}
    requests = []
    cursor = end
    while cursor >= start:
        q = urllib.parse.urlencode({"step": step, "limit": 1000, "end": cursor, "exclude_current_candle": "true"})
        url = f"{BASE}/{market}/?{q}"
        blob = get(url)
        js = json.loads(blob.decode())
        batch = js.get("data", {}).get("ohlc", [])
        requests.append({"market": market, "step": step, "end": cursor, "url": url, "payload_sha256": sha(blob), "rows": len(batch)})
        if not batch:
            break
        ts = [int(r["timestamp"]) for r in batch]
        for r in batch:
            t = int(r["timestamp"])
            if start <= t <= end:
                rows[t] = r
        earliest = min(ts)
        if earliest <= start:
            break
        nxt = earliest - step
        if nxt >= cursor:
            raise RuntimeError("Bitstamp pagination did not progress")
        cursor = nxt
        time.sleep(0.05)
    data = []
    for t in sorted(rows):
        r = rows[t]
        data.append({
            "open_time": pd.to_datetime(t, unit="s", utc=True),
            "availability_time": pd.to_datetime(t + step, unit="s", utc=True),
            "open": float(r["open"]), "high": float(r["high"]), "low": float(r["low"]), "close": float(r["close"]), "volume": float(r["volume"]),
        })
    return pd.DataFrame(data), requests


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="modern_bitstamp_regression")
    ap.add_argument("--start", default="2023-01-01T00:00:00Z")
    ap.add_argument("--end", default="2026-01-10T07:00:00Z")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    start = int(pd.Timestamp(a.start).timestamp()); end = int(pd.Timestamp(a.end).timestamp())
    manifests=[]; audits=[]
    for label, step in STEPS.items():
        d, reqs = collect("btcusd", step, start, end)
        if d.empty:
            raise SystemExit(f"no Bitstamp data for {label}")
        p=out/f"BTCUSD_{label}_modern.csv.gz"; d.to_csv(p,index=False,compression="gzip")
        t=pd.to_datetime(d.open_time,utc=True)
        env=((d.high<d[["open","close","low"]].max(axis=1))|(d.low>d[["open","close","high"]].min(axis=1)))
        expected_start=pd.Timestamp(a.start); expected_end=pd.Timestamp(a.end)
        out_of_range=((t<expected_start)|(t>expected_end)).sum()
        audits.append({"interval":label,"rows":len(d),"start":str(t.iloc[0]),"end":str(t.iloc[-1]),"duplicate_timestamps":int(t.duplicated().sum()),"monotonic":bool(t.is_monotonic_increasing),"ohlc_envelope_failures":int(env.sum()),"timestamp_out_of_range":int(out_of_range),"sha256":sha(p.read_bytes())})
        manifests.extend(reqs)
    ad=pd.DataFrame(audits); ad.to_csv(out/"integrity.csv",index=False); pd.DataFrame(manifests).to_csv(out/"request_manifest.csv",index=False)
    bad=ad[(ad.duplicate_timestamps!=0)|(~ad.monotonic)|(ad.ohlc_envelope_failures!=0)|(ad.timestamp_out_of_range!=0)]
    gate={"status":"PASS" if bad.empty else "FAIL","purpose":"MODERN_BITSTAMP_STATE_SOURCE_REGRESSION_DATA_ONLY","comparison_start":a.start,"comparison_cutoff":a.end,"performance_evaluation_allowed":False,"failed_series":int(len(bad)),"generated_at_utc":datetime.now(timezone.utc).isoformat()}
    (out/"DATA_GATE.json").write_text(json.dumps(gate,indent=2),encoding="utf-8")
    print(ad.to_string(index=False)); print(json.dumps(gate,indent=2))
    if not bad.empty: raise SystemExit("Bitstamp modern integrity gate failed")

if __name__ == "__main__":
    main()

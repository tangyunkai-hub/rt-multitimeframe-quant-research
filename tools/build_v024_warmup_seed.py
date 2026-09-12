from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

BINANCE = "https://data-api.binance.vision/api/v3/klines"
BITSTAMP = "https://www.bitstamp.net/api/v2/ohlc"
START = pd.Timestamp("2023-01-01T00:00:00Z")
FREEZE = pd.Timestamp("2026-09-12T02:00:00Z")
INTERVAL_MS = 15 * 60 * 1000
BITSTAMP_STEPS = {"12h": 43200, "1d": 86400}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "rtquant-v024-warmup-seed/1.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()


def collect_binance(loader=get):
    start_ms = int(START.timestamp() * 1000)
    last_open_ms = int((FREEZE - pd.Timedelta("15m")).timestamp() * 1000)
    cursor = start_ms
    rows = []
    requests = []
    while cursor <= last_open_ms:
        q = urllib.parse.urlencode({
            "symbol": "BTCUSDT", "interval": "15m", "limit": 1000,
            "startTime": cursor, "endTime": last_open_ms,
        })
        url = f"{BINANCE}?{q}"
        blob = loader(url)
        batch = json.loads(blob.decode("utf-8"))
        requests.append({"source":"binance_rest","url":url,"payload_sha256":sha256_bytes(blob),"rows":len(batch)})
        if not batch:
            break
        for r in batch:
            open_ms = int(r[0])
            availability = pd.to_datetime(open_ms + INTERVAL_MS, unit="ms", utc=True)
            if availability <= FREEZE:
                rows.append({
                    "open_time": pd.to_datetime(open_ms, unit="ms", utc=True),
                    "availability_time": availability,
                    "open": float(r[1]), "high": float(r[2]), "low": float(r[3]),
                    "close": float(r[4]), "volume": float(r[5]),
                })
        nxt = int(batch[-1][0]) + INTERVAL_MS
        if nxt <= cursor:
            raise RuntimeError("Binance pagination did not progress")
        cursor = nxt
        time.sleep(0.01)
    return pd.DataFrame(rows).drop_duplicates("open_time").sort_values("open_time"), requests


def collect_bitstamp(step: int, loader=get):
    start_open = int(START.timestamp())
    end_open = int((FREEZE - pd.Timedelta(seconds=step)).timestamp())
    rows = {}; requests=[]; cursor=end_open
    while cursor >= start_open:
        q = urllib.parse.urlencode({"step":step,"limit":1000,"end":cursor,"exclude_current_candle":"true"})
        url=f"{BITSTAMP}/btcusd/?{q}"
        blob=loader(url); js=json.loads(blob.decode("utf-8")); batch=js.get("data",{}).get("ohlc",[])
        requests.append({"source":"bitstamp_ohlc","step":step,"url":url,"payload_sha256":sha256_bytes(blob),"rows":len(batch)})
        if not batch: break
        ts=[int(r["timestamp"]) for r in batch]
        for r in batch:
            t=int(r["timestamp"]); avail=pd.to_datetime(t+step,unit="s",utc=True)
            if t>=start_open and avail<=FREEZE:
                rows[t]=r
        earliest=min(ts)
        if earliest<=start_open: break
        nxt=earliest-step
        if nxt>=cursor: raise RuntimeError("Bitstamp pagination did not progress")
        cursor=nxt; time.sleep(0.02)
    data=[]
    for t in sorted(rows):
        r=rows[t]
        data.append({"open_time":pd.to_datetime(t,unit="s",utc=True),"availability_time":pd.to_datetime(t+step,unit="s",utc=True),
                     "open":float(r["open"]),"high":float(r["high"]),"low":float(r["low"]),"close":float(r["close"]),"volume":float(r["volume"])})
    return pd.DataFrame(data),requests


def audit_frame(df: pd.DataFrame, *, name: str) -> dict:
    if df.empty: return {"name":name,"status":"FAIL","rows":0}
    t=pd.to_datetime(df.availability_time,utc=True)
    env=((df.high<df[["open","close","low"]].max(axis=1))|(df.low>df[["open","close","high"]].min(axis=1)))
    nonpos=(df[["open","high","low","close"]]<=0).any(axis=1)
    bad_time=(t>FREEZE)
    status="PASS" if int(t.duplicated().sum())==0 and t.is_monotonic_increasing and not env.any() and not nonpos.any() and not bad_time.any() else "FAIL"
    return {"name":name,"status":status,"rows":len(df),"start_availability":str(t.iloc[0]),"end_availability":str(t.iloc[-1]),
            "duplicate_timestamps":int(t.duplicated().sum()),"monotonic":bool(t.is_monotonic_increasing),
            "ohlc_envelope_failures":int(env.sum()),"nonpositive_price_rows":int(nonpos.sum()),"post_freeze_rows":int(bad_time.sum())}


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument("--out",default="v024_warmup_seed"); args=ap.parse_args()
    out=Path(args.out); (out/"binance").mkdir(parents=True,exist_ok=True); (out/"bitstamp").mkdir(parents=True,exist_ok=True)
    requests=[]; audits=[]; file_rows=[]
    b,req=collect_binance(); requests.extend(req); bp=out/"binance"/"BTCUSDT_15m_warmup.csv.gz"; b.to_csv(bp,index=False,compression="gzip"); audits.append(audit_frame(b,name="binance_btcusdt_15m")); file_rows.append((bp,len(b)))
    for label,step in BITSTAMP_STEPS.items():
        d,req=collect_bitstamp(step); requests.extend(req); p=out/"bitstamp"/f"BTCUSD_{label}_warmup.csv.gz"; d.to_csv(p,index=False,compression="gzip"); audits.append(audit_frame(d,name=f"bitstamp_btcusd_{label}")); file_rows.append((p,len(d)))
    pd.DataFrame(requests).to_csv(out/"source_request_manifest.csv",index=False)
    pd.DataFrame(audits).to_csv(out/"integrity.csv",index=False)
    if any(a["status"]!="PASS" for a in audits): raise SystemExit("warmup seed integrity failed")
    files=[]
    for p,rows in file_rows:
        files.append({"path":str(p.relative_to(out)).replace('\\','/'),"sha256":sha256_file(p),"rows":int(rows)})
    root_text=''.join(f"{x['path']} {x['sha256']}\n" for x in sorted(files,key=lambda x:x['path']))
    root=hashlib.sha256(root_text.encode()).hexdigest()
    contract={
        "classification":"V024_CONSUMED_PRE_FREEZE_WARMUP_SEED",
        "status":"PASS",
        "candidate_freeze_boundary_utc_inclusive_for_warmup":FREEZE.isoformat(),
        "warmup_start_utc":START.isoformat(),
        "purpose":"Indicator/state initialization only; never prospective evidence.",
        "performance_evaluation_allowed":False,
        "candidate_b_judgement_allowed":False,
        "prospective_evidence_rows":0,
        "files":files,
        "seed_root_sha256":root,
        "source_request_manifest_sha256":sha256_file(out/"source_request_manifest.csv"),
        "integrity_sha256":sha256_file(out/"integrity.csv"),
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
    }
    (out/"WARMUP_SEED_CONTRACT.json").write_text(json.dumps(contract,indent=2),encoding="utf-8")
    print(json.dumps(contract,indent=2))

if __name__=="__main__": main()

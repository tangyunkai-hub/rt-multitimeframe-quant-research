from __future__ import annotations

import argparse, hashlib, io, json, time, urllib.error, urllib.parse, urllib.request, zipfile
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

BINANCE_BASE = "https://data.binance.vision/data/spot/monthly/klines"
BITSTAMP_BASE = "https://www.bitstamp.net/api/v2/ohlc"
COLS = ["open_time_ms","open","high","low","close","volume","close_time_ms","quote_asset_volume","number_of_trades","taker_buy_base_asset_volume","taker_buy_quote_asset_volume","ignore"]
TFSEC = {"15m":900,"2h":7200,"8h":28800,"3d":259200}
BSTEPS = {"12h":43200,"1d":86400}

def sha(b): return hashlib.sha256(b).hexdigest()

def get(url, retries=4):
    last=None
    for i in range(retries):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"rtquant-external-validation/1.0"})
            with urllib.request.urlopen(req,timeout=60) as r: return r.read()
        except urllib.error.HTTPError as e:
            if e.code==404: raise
            last=e
        except Exception as e: last=e
        time.sleep(min(2**i,8))
    raise RuntimeError(f"download failed: {url}: {last}")

def checksum(text):
    p=text.strip().splitlines()[0].replace("*"," ").split()
    return p[0].lower(), (p[-1] if len(p)>1 else None)

def read_zip(blob):
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        names=[n for n in z.namelist() if n.lower().endswith('.csv')]
        if len(names)!=1: raise ValueError(f"expected one csv, got {names}")
        df=pd.read_csv(io.BytesIO(z.read(names[0])),header=None)
    if df.shape[1]!=len(COLS): raise ValueError(f"unexpected Binance columns: {df.shape[1]}")
    df.columns=COLS
    for c in ["open_time_ms","close_time_ms","number_of_trades"]: df[c]=pd.to_numeric(df[c],errors='raise').astype('int64')
    for c in ["open","high","low","close","volume"]: df[c]=pd.to_numeric(df[c],errors='raise').astype(float)
    return df

def audit(df,time_col,step):
    t=pd.to_datetime(df[time_col],utc=True)
    gaps=t.diff().dropna(); exp=pd.Timedelta(seconds=step); bad=gaps[gaps!=exp]
    env=((df.high<df[["open","close","low"]].max(axis=1))|(df.low>df[["open","close","high"]].min(axis=1)))
    return {"rows":len(df),"start":str(t.iloc[0]) if len(t) else None,"end":str(t.iloc[-1]) if len(t) else None,
            "duplicate_timestamps":int(t.duplicated().sum()),"monotonic":bool(t.is_monotonic_increasing),
            "ohlc_envelope_failures":int(env.sum()),"nonstandard_gap_count":int(len(bad)),
            "max_gap_seconds":float(bad.max().total_seconds()) if len(bad) else 0.0}

def binance(symbol,interval,y0,y1,out):
    frames=[]; manifest=[]; first=None; missing=[]
    for y in range(y0,y1+1):
      for m in range(1,13):
        ym=f"{y:04d}-{m:02d}"; name=f"{symbol}-{interval}-{ym}.zip"; url=f"{BINANCE_BASE}/{symbol}/{interval}/{name}"
        try: blob=get(url)
        except urllib.error.HTTPError as e:
            if e.code==404:
                manifest.append({"symbol":symbol,"interval":interval,"month":ym,"status":"404_prelisting_or_missing","url":url})
                if first is not None: missing.append(ym)
                continue
            raise
        local=sha(blob); remote,cname=checksum(get(url+'.CHECKSUM').decode('utf-8','replace'))
        if local!=remote: raise RuntimeError(f"checksum mismatch: {name}")
        d=read_zip(blob); frames.append(d); first=first or ym
        manifest.append({"symbol":symbol,"interval":interval,"month":ym,"status":"ok","url":url,"checksum_url":url+'.CHECKSUM',"remote_sha256":remote,"local_sha256":local,"checksum_filename":cname,"rows":len(d)})
    if not frames: raise RuntimeError(f"no data: {symbol} {interval}")
    if missing: raise RuntimeError(f"missing months after listing: {symbol} {interval} {missing}")
    d=pd.concat(frames,ignore_index=True).sort_values('open_time_ms').drop_duplicates('open_time_ms',keep='last').reset_index(drop=True)
    d['open_time']=pd.to_datetime(d.open_time_ms,unit='ms',utc=True); d['availability_time']=d.open_time+pd.to_timedelta(TFSEC[interval],unit='s')
    d=d[["open_time","availability_time","open","high","low","close","volume","number_of_trades"]]
    p=out/'binance'/f"{symbol}_{interval}_{y0}-{y1}.csv.gz"; p.parent.mkdir(parents=True,exist_ok=True); d.to_csv(p,index=False,compression='gzip')
    a=audit(d,'open_time',TFSEC[interval]); a.update({"source":"Binance","symbol":symbol,"interval":interval,"first_success_month":first,"normalized_file":str(p.relative_to(out)),"normalized_sha256":sha(p.read_bytes())})
    return d,manifest,a

def bitstamp_rows(market,step,start,end):
    rows={}; reqs=[]; cursor=end
    while cursor>=start:
        q=urllib.parse.urlencode({"step":step,"limit":1000,"end":cursor,"exclude_current_candle":"true"}); url=f"{BITSTAMP_BASE}/{market}/?{q}"
        blob=get(url); js=json.loads(blob.decode()); batch=js.get('data',{}).get('ohlc',[])
        reqs.append({"market":market,"step":step,"end":cursor,"url":url,"payload_sha256":sha(blob),"rows":len(batch)})
        if not batch: break
        ts=[int(r['timestamp']) for r in batch]
        for r in batch:
            t=int(r['timestamp'])
            if start<=t<=end: rows[t]=r
        earliest=min(ts)
        if earliest<=start: break
        nxt=earliest-step
        if nxt>=cursor: raise RuntimeError('Bitstamp pagination did not progress')
        cursor=nxt; time.sleep(.05)
    if not rows: raise RuntimeError(f"no Bitstamp rows: {market} {step}")
    data=[]
    for t in sorted(rows):
        r=rows[t]; data.append({"open_time":pd.to_datetime(t,unit='s',utc=True),"availability_time":pd.to_datetime(t+step,unit='s',utc=True),"open":float(r['open']),"high":float(r['high']),"low":float(r['low']),"close":float(r['close']),"volume":float(r['volume'])})
    return pd.DataFrame(data),reqs

def bitstamp(market,label,y0,y1,out):
    step=BSTEPS[label]; start=int(datetime(y0,1,1,tzinfo=timezone.utc).timestamp()); end=int(datetime(y1+1,1,1,tzinfo=timezone.utc).timestamp())-step
    d,reqs=bitstamp_rows(market,step,start,end); p=out/'bitstamp'/f"{market.upper()}_{label}_{y0}-{y1}.csv.gz"; p.parent.mkdir(parents=True,exist_ok=True); d.to_csv(p,index=False,compression='gzip')
    a=audit(d,'open_time',step); a.update({"source":"Bitstamp","symbol":market.upper(),"interval":label,"normalized_file":str(p.relative_to(out)),"normalized_sha256":sha(p.read_bytes())})
    return d,reqs,a

def parity(base,native,interval):
    b=base.copy().set_index(pd.to_datetime(base.availability_time,utc=True)); n=native.copy().set_index(pd.to_datetime(native.availability_time,utc=True))
    r=b[["open","high","low","close","volume"]].resample(interval,label='right',closed='right',origin='epoch').agg({"open":"first","high":"max","low":"min","close":"last","volume":"sum"}).dropna(subset=["open","high","low","close"])
    common=r.index.intersection(n.index)
    if not len(common): return {"interval":interval,"common_bars":0,"mismatch_bars":None,"match_rate":None,"max_abs_price_diff":None}
    diff=(r.loc[common,["open","high","low","close"]]-n.loc[common,["open","high","low","close"]]).abs(); mm=(diff>1e-8).any(axis=1)
    return {"interval":interval,"common_bars":len(common),"mismatch_bars":int(mm.sum()),"match_rate":float(1-mm.mean()),"max_abs_price_diff":float(diff.to_numpy().max()),"start":str(common.min()),"end":str(common.max())}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',default='external_history_2017_2022'); ap.add_argument('--start-year',type=int,default=2017); ap.add_argument('--end-year',type=int,default=2022); a=ap.parse_args()
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True); bm=[]; sm=[]; audits=[]; loaded={}
    for symbol in ['BTCUSDT','ETHUSDT']:
      for interval in ['15m','2h','8h','3d']:
        print('[binance]',symbol,interval,flush=True); d,recs,au=binance(symbol,interval,a.start_year,a.end_year,out); loaded[symbol,interval]=d; bm+=recs; audits.append(au)
    for market in ['btcusd','ethusd']:
      for label in ['12h','1d']:
        print('[bitstamp]',market,label,flush=True); d,recs,au=bitstamp(market,label,a.start_year,a.end_year,out); sm+=recs; audits.append(au)
    pars=[]
    for symbol in ['BTCUSDT','ETHUSDT']:
      for interval in ['2h','8h','3d']:
        p=parity(loaded[symbol,'15m'],loaded[symbol,interval],interval); p['symbol']=symbol; pars.append(p)
    pd.DataFrame(bm).to_csv(out/'binance_source_manifest.csv',index=False); pd.DataFrame(sm).to_csv(out/'bitstamp_request_manifest.csv',index=False); pd.DataFrame(audits).to_csv(out/'data_integrity_audit.csv',index=False); pd.DataFrame(pars).to_csv(out/'binance_native_parity.csv',index=False)
    hard=[x for x in audits if x['duplicate_timestamps'] or not x['monotonic'] or x['ohlc_envelope_failures']]+[x for x in pars if x.get('mismatch_bars') not in (0,None)]
    summary={"dataset":"RT external historical validation dataset","period":f"{a.start_year}-01-01 through {a.end_year}-12-31","classification":"EXTERNAL_HISTORICAL_VALIDATION_NOT_PROSPECTIVE","binance_symbols":["BTCUSDT","ETHUSDT"],"binance_intervals":["15m","2h","8h","3d"],"bitstamp_markets":["btcusd","ethusd"],"bitstamp_intervals":["12h","1d"],"hard_failure_count":len(hard),"hard_failures":hard,"generated_at_utc":datetime.now(timezone.utc).isoformat(),"anti_overfit_rule":"No Candidate A/B semantic, threshold, cost, or sizing change is permitted based on these results."}
    (out/'DATASET_SUMMARY.json').write_text(json.dumps(summary,indent=2)); print(json.dumps(summary,indent=2),flush=True)
    if hard: raise SystemExit(f"data gate failed: {len(hard)} hard failures")

if __name__=='__main__': main()

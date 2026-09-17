#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, io, json, urllib.request, urllib.error, zipfile
from datetime import date, timedelta
from pathlib import Path

ROOT='https://data.binance.vision/data/futures/um'
START=date(2019,9,8); END=date(2026,9,15)
OUT=Path('broad_discovery_cycle1'); RAW=OUT/'raw'; RAW.mkdir(parents=True,exist_ok=True)
def sha(b): return hashlib.sha256(b).hexdigest()
def fetch(url):
    with urllib.request.urlopen(url,timeout=45) as r: return r.read()
def parse_zip(blob):
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        names=[n for n in z.namelist() if n.endswith('.csv')]
        if len(names)!=1: raise SystemExit(f'unexpected zip members {names}')
        rr=list(csv.reader(io.StringIO(z.read(names[0]).decode('utf-8'))))
        if rr and rr[0] and not rr[0][0].isdigit(): rr=rr[1:]
        return rr

def month_iter(a,b):
    y,m=a.year,a.month
    while (y,m)<=(b.year,b.month):
        yield y,m
        m+=1
        if m==13: y,m=y+1,1

def daily_range(a,b):
    d=a
    while d<=b:
        yield d; d+=timedelta(days=1)

rows=[]; manifest=[]
for y,m in month_iter(date(2019,9,1),date(2026,8,1)):
    name=f'BTCUSDT-1d-{y:04d}-{m:02d}.zip'; url=f'{ROOT}/monthly/klines/BTCUSDT/1d/{name}'
    try:
        blob=fetch(url); rr=parse_zip(blob); rows.extend(rr); manifest.append({'mode':'monthly','file':name,'url':url,'sha256':sha(blob),'rows':len(rr)})
    except urllib.error.HTTPError as e:
        if e.code!=404: raise
        # Binance USD-M monthly archive does not cover some early launch months; use official daily archives only for that missing month.
        first=date(y,m,1); nextm=date(y+1,1,1) if m==12 else date(y,m+1,1); last=nextm-timedelta(days=1)
        for d in daily_range(max(first,START),min(last,END)):
            ds=d.isoformat(); dn=f'BTCUSDT-1d-{ds}.zip'; du=f'{ROOT}/daily/klines/BTCUSDT/1d/{dn}'
            blob=fetch(du); rr=parse_zip(blob); rows.extend(rr); manifest.append({'mode':'daily_fallback','file':dn,'url':du,'sha256':sha(blob),'rows':len(rr)})
# Frozen partial current month must come from official daily files; never use a future-complete monthly archive.
for d in daily_range(date(2026,9,1),END):
    ds=d.isoformat(); name=f'BTCUSDT-1d-{ds}.zip'; url=f'{ROOT}/daily/klines/BTCUSDT/1d/{name}'
    blob=fetch(url); rr=parse_zip(blob); rows.extend(rr); manifest.append({'mode':'daily_cutoff','file':name,'url':url,'sha256':sha(blob),'rows':len(rr)})

lo=1567900800000; hi=1789430400000
rows=[r for r in rows if r and lo<=int(r[0])<=hi]; rows.sort(key=lambda r:int(r[0]))
opens=[int(r[0]) for r in rows]
if not opens or opens[0]!=lo or opens[-1]!=hi: raise SystemExit(f'coverage mismatch {opens[:1]}..{opens[-1:]}')
if len(opens)!=len(set(opens)): raise SystemExit('duplicate openTime')
if any(b-a!=86400000 for a,b in zip(opens,opens[1:])): raise SystemExit('daily gap/nonmonotonic')
for r in rows:
    o,h,l,c=map(float,r[1:5])
    if min(o,h,l,c)<=0 or h<max(o,c,l) or l>min(o,c,h): raise SystemExit(f'bad OHLC {r[:5]}')
header=['open_time','open','high','low','close','volume','close_time','quote_volume','trades','taker_buy_base','taker_buy_quote','ignore']
out=io.StringIO(); w=csv.writer(out,lineterminator='\n'); w.writerow(header); w.writerows(rows)
data=out.getvalue().encode(); (OUT/'btc_usdt_um_1d_2019-09-08_2026-09-15.csv').write_bytes(data)
summary={'status':'PASS','performance_evaluation_allowed':False,'rows':len(rows),'first_open_time':opens[0],'last_open_time':opens[-1],'duplicate_open_time':0,'daily_gap_count':0,'ohlc_invalid':0,'normalized_sha256':sha(data),'source_files':manifest}
(OUT/'source_manifest.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='source_files'},indent=2))
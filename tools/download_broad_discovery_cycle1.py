#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, io, json, urllib.request, zipfile
from datetime import date
from pathlib import Path

BASE='https://data.binance.vision/data/futures/um/monthly/klines/BTCUSDT/1d'
START=date(2019,9,1); END=date(2026,9,1)
OUT=Path('broad_discovery_cycle1'); RAW=OUT/'raw'; RAW.mkdir(parents=True,exist_ok=True)

def months(a,b):
    y,m=a.year,a.month
    while (y,m)<=(b.year,b.month):
        yield y,m
        m+=1
        if m==13:y,m=y+1,1

def sha(b): return hashlib.sha256(b).hexdigest()
rows=[]; manifest=[]
for y,m in months(START,END):
    name=f'BTCUSDT-1d-{y:04d}-{m:02d}.zip'; url=f'{BASE}/{name}'
    try:
        with urllib.request.urlopen(url,timeout=30) as r: blob=r.read()
    except Exception as e:
        raise SystemExit(f'download failed {url}: {e}')
    (RAW/name).write_bytes(blob)
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        members=z.namelist()
        if len(members)!=1: raise SystemExit(f'unexpected members {name}: {members}')
        text=z.read(members[0]).decode('utf-8')
    rr=list(csv.reader(io.StringIO(text)))
    if rr and rr[0] and not rr[0][0].isdigit(): rr=rr[1:]
    manifest.append({'file':name,'url':url,'sha256':sha(blob),'rows':len(rr)})
    rows.extend(rr)
# Binance kline columns; restrict exact frozen consumed-development interval.
lo=1567900800000; hi=1789430400000
rows=[r for r in rows if r and lo<=int(r[0])<=hi]
rows.sort(key=lambda r:int(r[0]))
opens=[int(r[0]) for r in rows]
if len(opens)!=len(set(opens)): raise SystemExit('duplicate openTime')
if any(b-a!=86400000 for a,b in zip(opens,opens[1:])): raise SystemExit('daily gap/nonmonotonic')
if opens[0]!=lo or opens[-1]!=hi: raise SystemExit(f'coverage mismatch {opens[0]}..{opens[-1]}')
for r in rows:
    o,h,l,c=map(float,r[1:5])
    if min(o,h,l,c)<=0 or h<max(o,c,l) or l>min(o,c,h): raise SystemExit(f'bad OHLC {r[:5]}')
header=['open_time','open','high','low','close','volume','close_time','quote_volume','trades','taker_buy_base','taker_buy_quote','ignore']
out=io.StringIO(); w=csv.writer(out,lineterminator='\n'); w.writerow(header); w.writerows(rows)
data=out.getvalue().encode(); (OUT/'btc_usdt_um_1d_2019-09-08_2026-09-15.csv').write_bytes(data)
summary={'status':'PASS','performance_evaluation_allowed':False,'rows':len(rows),'first_open_time':opens[0],'last_open_time':opens[-1],'duplicate_open_time':0,'daily_gap_count':0,'normalized_sha256':sha(data),'source_files':manifest}
(OUT/'source_manifest.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='source_files'},indent=2))

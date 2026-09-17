#!/usr/bin/env python3
import csv, hashlib, io, json, urllib.parse, urllib.request
from pathlib import Path
OUT=Path('broad_discovery_cycle1'); OUT.mkdir(parents=True,exist_ok=True)
URL='https://fapi.binance.com/fapi/v1/klines'; LO=1567900800000; HI=1789430400000; DAY=86400000
rows=[]; start=LO; source=[]
while start<=HI:
    q=urllib.parse.urlencode({'symbol':'BTCUSDT','interval':'1d','startTime':start,'endTime':HI+DAY-1,'limit':1500})
    u=URL+'?'+q
    req=urllib.request.Request(u,headers={'User-Agent':'rt-quant-research/1.0'})
    with urllib.request.urlopen(req,timeout=60) as r: blob=r.read()
    batch=json.loads(blob)
    if not batch: break
    rows.extend(batch); source.append({'url':u,'rows':len(batch),'response_sha256':hashlib.sha256(blob).hexdigest()})
    nxt=int(batch[-1][0])+DAY
    if nxt<=start: raise SystemExit('pagination did not advance')
    start=nxt
rows=[r for r in rows if LO<=int(r[0])<=HI]; rows.sort(key=lambda r:int(r[0]))
opens=[int(r[0]) for r in rows]
if not opens or opens[0]!=LO or opens[-1]!=HI: raise SystemExit(f'coverage mismatch {opens[:1]}..{opens[-1:]}')
if len(opens)!=len(set(opens)): raise SystemExit('duplicate openTime')
if any(b-a!=DAY for a,b in zip(opens,opens[1:])): raise SystemExit('daily gap/nonmonotonic')
for r in rows:
    o,h,l,c=map(float,r[1:5])
    if min(o,h,l,c)<=0 or h<max(o,c,l) or l>min(o,c,h): raise SystemExit(f'bad OHLC {r[:5]}')
header=['open_time','open','high','low','close','volume','close_time','quote_volume','trades','taker_buy_base','taker_buy_quote','ignore']
s=io.StringIO(); w=csv.writer(s,lineterminator='\n'); w.writerow(header); w.writerows(rows)
data=s.getvalue().encode(); p=OUT/'btc_usdt_um_1d_2019-09-08_2026-09-15.csv'; p.write_bytes(data)
summary={'status':'PASS','performance_evaluation_allowed':False,'source':'Binance USD-M public REST /fapi/v1/klines','rows':len(rows),'first_open_time':opens[0],'last_open_time':opens[-1],'duplicate_open_time':0,'daily_gap_count':0,'ohlc_invalid':0,'normalized_sha256':hashlib.sha256(data).hexdigest(),'requests':source}
(OUT/'source_manifest.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='requests'},indent=2))
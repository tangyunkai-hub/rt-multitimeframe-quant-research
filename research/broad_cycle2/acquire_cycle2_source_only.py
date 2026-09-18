#!/usr/bin/env python3
"""SOURCE-ONLY acquisition for Broad Discovery Cycle-2.
No strategy signal/performance is computed here.
Frozen dev cutoff: 2019-09-08 through 2026-09-15 UTC.
Funding native start is accepted from first official observation; no interpolation.
Premium-index 1d native start is accepted from first official observation; no interpolation.
"""
from __future__ import annotations
import csv, hashlib, json, time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen, Request

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'source_freeze'
OUT.mkdir(parents=True, exist_ok=True)
BASE='https://fapi.binance.com'
START=1567900800000  # 2019-09-08 00:00 UTC
END=1789516799999    # 2026-09-15 23:59:59.999 UTC

def get(path, params):
    u=BASE+path+'?'+urlencode(params)
    for k in range(6):
        try:
            with urlopen(Request(u,headers={'User-Agent':'rt-quant-research/1.0'}),timeout=30) as r:
                return json.loads(r.read())
        except Exception:
            if k==5: raise
            time.sleep(2**k)

def canon_json_bytes(obj):
    return (json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n').encode()

def sha(b): return hashlib.sha256(b).hexdigest()

# Funding: deterministic forward pagination, canonical fields only.
fund=[]; cursor=START
while cursor<=END:
    rows=get('/fapi/v1/fundingRate',{'symbol':'BTCUSDT','startTime':cursor,'endTime':END,'limit':1000})
    if not rows: break
    for r in rows:
        t=int(r['fundingTime'])
        if START<=t<=END:
            fund.append({'symbol':r['symbol'],'fundingTime':t,'fundingRate':str(r['fundingRate']),'rateType':str(r.get('rateType','Regular'))})
    nxt=int(rows[-1]['fundingTime'])+1
    if nxt<=cursor: raise RuntimeError('non-advancing funding pagination')
    cursor=nxt
    if len(rows)<1000: break
fund=sorted(fund,key=lambda x:(x['fundingTime'],x['symbol'],x['fundingRate'],x['rateType']))
if len({(x['fundingTime'],x['symbol']) for x in fund})!=len(fund): raise RuntimeError('duplicate funding key')
fb=canon_json_bytes(fund); (OUT/'btcusdt_usdm_funding_20190908_20260915.json').write_bytes(fb)

# Premium index: official 1d klines, deterministic pagination.
prem=[]; cursor=START
while cursor<=END:
    rows=get('/fapi/v1/premiumIndexKlines',{'symbol':'BTCUSDT','interval':'1d','startTime':cursor,'endTime':END,'limit':1500})
    if not rows: break
    for r in rows:
        ot=int(r[0])
        if START<=ot<=END:
            prem.append({'openTime':ot,'open':str(r[1]),'high':str(r[2]),'low':str(r[3]),'close':str(r[4])})
    nxt=int(rows[-1][0])+86400000
    if nxt<=cursor: raise RuntimeError('non-advancing premium pagination')
    cursor=nxt
    if len(rows)<1500: break
prem=sorted(prem,key=lambda x:x['openTime'])
if len({x['openTime'] for x in prem})!=len(prem): raise RuntimeError('duplicate premium openTime')
pb=canon_json_bytes(prem); (OUT/'btcusdt_usdm_premium_1d_20190908_20260915.json').write_bytes(pb)

manifest={
 'classification':'SOURCE_ONLY_PRE_OUTCOME',
 'symbol':'BTCUSDT','market':'Binance USD-M perpetual',
 'frozen_dev_start_ms':START,'frozen_dev_end_ms':END,
 'funding':{'endpoint':'/fapi/v1/fundingRate','rows':len(fund),'first_ms':fund[0]['fundingTime'] if fund else None,'last_ms':fund[-1]['fundingTime'] if fund else None,'sha256':sha(fb)},
 'premium_1d':{'endpoint':'/fapi/v1/premiumIndexKlines','rows':len(prem),'first_ms':prem[0]['openTime'] if prem else None,'last_ms':prem[-1]['openTime'] if prem else None,'sha256':sha(pb)},
 'rules':['no interpolation','no signal computation','no performance computation','canonical deterministic JSON'],
}
mb=canon_json_bytes(manifest); (OUT/'cycle2_source_manifest.json').write_bytes(mb)
(OUT/'cycle2_source_manifest.sha256').write_text(sha(mb)+'  cycle2_source_manifest.json\n')
print(json.dumps(manifest,indent=2,sort_keys=True))

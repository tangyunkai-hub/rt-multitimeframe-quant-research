#!/usr/bin/env python3
"""SOURCE-ONLY acquisition for Broad Discovery Cycle-2.
No strategy signal/performance is computed here.
Frozen dev cutoff: 2019-09-08 through 2026-09-15 UTC.
Uses Binance's first-party public Vision archive so GitHub-hosted compute does not
need fapi.binance.com (which returns HTTP 451 from the hosted-runner region).
No interpolation; missing unpublished archive objects are retained as missing.
"""
from __future__ import annotations
import csv, hashlib, io, json, time, zipfile
from datetime import date, timedelta
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen, Request

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'source_freeze'
OUT.mkdir(parents=True, exist_ok=True)
VISION='https://data.binance.vision/data/futures/um'
START=1567900800000  # 2019-09-08 00:00 UTC
END=1789516799999    # 2026-09-15 23:59:59.999 UTC

def fetch_bytes(url):
    for k in range(6):
        try:
            with urlopen(Request(url,headers={'User-Agent':'rt-quant-research/1.0'}),timeout=45) as r:
                return r.read()
        except HTTPError as e:
            if e.code==404: return None
            if k==5: raise
        except Exception:
            if k==5: raise
        time.sleep(2**k)

def unzip_csv(blob):
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        names=[n for n in z.namelist() if n.lower().endswith('.csv')]
        if len(names)!=1: raise RuntimeError(f'expected one CSV, got {names}')
        raw=z.read(names[0]).decode('utf-8-sig')
    return list(csv.reader(io.StringIO(raw)))

def canon_json_bytes(obj):
    return (json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n').encode()

def sha(b): return hashlib.sha256(b).hexdigest()

def months(a,b):
    y,m=a.year,a.month
    while (y,m)<=(b.year,b.month):
        yield y,m
        m+=1
        if m==13: y,m=y+1,1

def parse_funding(rows):
    out=[]
    if not rows: return out
    header=[x.strip().lower() for x in rows[0]]
    has_header=any(x in header for x in ('calc_time','fundingtime','funding_time'))
    data=rows[1:] if has_header else rows
    if has_header:
        idx={k:i for i,k in enumerate(header)}
        ti=idx.get('calc_time',idx.get('fundingtime',idx.get('funding_time')))
        ri=idx.get('last_funding_rate',idx.get('fundingrate',idx.get('funding_rate')))
        ii=idx.get('funding_interval_hours')
        if ti is None or ri is None: raise RuntimeError(f'unknown funding header {rows[0]}')
        for r in data:
            if not r: continue
            out.append({'symbol':'BTCUSDT','fundingTime':int(r[ti]),'fundingRate':str(r[ri]),
                        'fundingIntervalHours':str(r[ii]) if ii is not None and ii<len(r) else '8'})
    else:
        # Binance Vision historical funding schema: calc_time, funding_interval_hours, last_funding_rate
        for r in data:
            if len(r)<3: continue
            out.append({'symbol':'BTCUSDT','fundingTime':int(r[0]),'fundingRate':str(r[-1]),
                        'fundingIntervalHours':str(r[1])})
    return out

def parse_premium(rows):
    out=[]
    if not rows: return out
    header=[x.strip().lower() for x in rows[0]]
    has_header=('open_time' in header or 'opentime' in header)
    data=rows[1:] if has_header else rows
    if has_header:
        idx={k:i for i,k in enumerate(header)}
        oi=idx.get('open_time',idx.get('opentime'))
        for r in data:
            if not r: continue
            out.append({'openTime':int(r[oi]),'open':str(r[1]),'high':str(r[2]),'low':str(r[3]),'close':str(r[4])})
    else:
        for r in data:
            if len(r)<5: continue
            out.append({'openTime':int(r[0]),'open':str(r[1]),'high':str(r[2]),'low':str(r[3]),'close':str(r[4])})
    return out

# Use complete monthly archives through 2026-08, then daily archives for frozen Sep-2026 edge.
fund=[]; prem=[]; source_objects=[]; missing=[]
for y,m in months(date(2019,9,1),date(2026,8,1)):
    ym=f'{y:04d}-{m:02d}'
    specs=[
      ('funding',f'{VISION}/monthly/fundingRate/BTCUSDT/BTCUSDT-fundingRate-{ym}.zip',parse_funding),
      ('premium',f'{VISION}/monthly/premiumIndexKlines/BTCUSDT/1d/BTCUSDT-1d-{ym}.zip',parse_premium),
    ]
    for kind,url,parser in specs:
        blob=fetch_bytes(url)
        if blob is None:
            missing.append({'kind':kind,'url':url}); continue
        rows=parser(unzip_csv(blob))
        source_objects.append({'kind':kind,'url':url,'zip_sha256':sha(blob),'parsed_rows':len(rows)})
        (fund if kind=='funding' else prem).extend(rows)

for d in (date(2026,9,1)+timedelta(days=i) for i in range(15)):
    ds=d.isoformat()
    specs=[
      ('funding',f'{VISION}/daily/fundingRate/BTCUSDT/BTCUSDT-fundingRate-{ds}.zip',parse_funding),
      ('premium',f'{VISION}/daily/premiumIndexKlines/BTCUSDT/1d/BTCUSDT-1d-{ds}.zip',parse_premium),
    ]
    for kind,url,parser in specs:
        blob=fetch_bytes(url)
        if blob is None:
            missing.append({'kind':kind,'url':url}); continue
        rows=parser(unzip_csv(blob))
        source_objects.append({'kind':kind,'url':url,'zip_sha256':sha(blob),'parsed_rows':len(rows)})
        (fund if kind=='funding' else prem).extend(rows)

fund=[x for x in fund if START<=x['fundingTime']<=END]
fund=sorted(fund,key=lambda x:(x['fundingTime'],x['symbol']))
if len({(x['fundingTime'],x['symbol']) for x in fund})!=len(fund): raise RuntimeError('duplicate funding key')
fb=canon_json_bytes(fund); (OUT/'btcusdt_usdm_funding_20190908_20260915.json').write_bytes(fb)

prem=[x for x in prem if START<=x['openTime']<=END]
prem=sorted(prem,key=lambda x:x['openTime'])
if len({x['openTime'] for x in prem})!=len(prem): raise RuntimeError('duplicate premium openTime')
for x in prem:
    o,h,l,c=map(float,(x['open'],x['high'],x['low'],x['close']))
    if not (l<=min(o,c)<=max(o,c)<=h): raise RuntimeError(f'invalid premium OHLC {x}')
pb=canon_json_bytes(prem); (OUT/'btcusdt_usdm_premium_1d_20190908_20260915.json').write_bytes(pb)

manifest={
 'classification':'SOURCE_ONLY_PRE_OUTCOME','source':'Binance Vision first-party public archive',
 'symbol':'BTCUSDT','market':'Binance USD-M perpetual',
 'frozen_dev_start_ms':START,'frozen_dev_end_ms':END,
 'funding':{'rows':len(fund),'first_ms':fund[0]['fundingTime'] if fund else None,'last_ms':fund[-1]['fundingTime'] if fund else None,'sha256':sha(fb)},
 'premium_1d':{'rows':len(prem),'first_ms':prem[0]['openTime'] if prem else None,'last_ms':prem[-1]['openTime'] if prem else None,'sha256':sha(pb)},
 'source_objects':source_objects,'missing_objects':missing,
 'rules':['no interpolation','no signal computation','no performance computation','canonical deterministic JSON','preserve source-object SHA256s'],
}
mb=canon_json_bytes(manifest); (OUT/'cycle2_source_manifest.json').write_bytes(mb)
(OUT/'cycle2_source_manifest.sha256').write_text(sha(mb)+'  cycle2_source_manifest.json\n')
print(json.dumps({k:v for k,v in manifest.items() if k not in ('source_objects','missing_objects')},indent=2,sort_keys=True))
print('source_objects',len(source_objects),'missing_objects',len(missing))

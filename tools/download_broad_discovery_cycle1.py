#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, io, json, urllib.request, urllib.error, zipfile, xml.etree.ElementTree as ET
from datetime import date, timedelta
from pathlib import Path

ROOT='https://data.binance.vision/data/futures/um'
START=date(2019,9,8); END=date(2026,9,15)
OUT=Path('broad_discovery_cycle1'); OUT.mkdir(parents=True,exist_ok=True)
def sha(b): return hashlib.sha256(b).hexdigest()
def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':'rt-quant-research/1.0'})
    with urllib.request.urlopen(req,timeout=60) as r: return r.read()
def parse_zip(blob):
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        names=[n for n in z.namelist() if n.endswith('.csv')]
        if len(names)!=1: raise SystemExit(f'unexpected zip members {names}')
        rr=list(csv.reader(io.StringIO(z.read(names[0]).decode('utf-8'))))
        if rr and rr[0] and not rr[0][0].isdigit(): rr=rr[1:]
        return rr

def list_keys(prefix):
    # Binance Vision exposes an S3-style prefix listing at its public root.
    url='https://data.binance.vision/?prefix='+urllib.parse.quote(prefix,safe='/')
    blob=fetch(url); root=ET.fromstring(blob); keys=[]
    for el in root.iter():
        if el.tag.endswith('Key') and el.text: keys.append(el.text)
    return sorted(keys)

import urllib.parse
prefix='data/futures/um/daily/klines/BTCUSDT/1d/'
keys=list_keys(prefix)
zips=[k for k in keys if k.endswith('.zip') and 'CHECKSUM' not in k]
coverage={'status':'ARCHIVE_COVERAGE_PROBE','performance_evaluation_allowed':False,'prefix':prefix,'zip_count':len(zips),'first_zip':zips[0] if zips else None,'last_zip':zips[-1] if zips else None}
(OUT/'archive_coverage_probe.json').write_text(json.dumps(coverage,indent=2,sort_keys=True)+'\n')
print(json.dumps(coverage,indent=2))
if not zips: raise SystemExit('official archive listing returned no daily BTCUSDT 1d zip keys')

# This probe intentionally does not compute candidate performance. It establishes the exact official archive boundary
# so the next frozen acquisition can combine only a provenance-hashed missing prefix (if any) with official archives.

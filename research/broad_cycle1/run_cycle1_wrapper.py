#!/usr/bin/env python3
"""Data-engineering bridge for the frozen Cycle-1 runner.

Strategy/performance code in run_cycle1.py remains untouched. This wrapper only
repairs Binance Vision archive availability:
1) 2019-09 is served from the previously audited/persisted official Binance
   connector bootstrap because the launch-era monthly object is absent.
2) Any other missing monthly Vision kline object is reconstructed *only* from
   official Binance Vision daily ZIPs for that same calendar month.
No price transformation, interpolation, signal logic, cost rule, horizon, or
candidate definition is changed.
"""
import calendar
import io
import re
import runpy
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ORIG_URLOPEN = urllib.request.urlopen
SEP2019 = "https://data.binance.vision/data/futures/um/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2019-09.zip"
BOOT = Path("research/broad_cycle1/bootstrap_btcusdt_um_1d_2019-09.csv")
MONTH_RE = re.compile(r"^https://data\.binance\.vision/data/futures/um/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-(\d{4})-(\d{2})\.zip$")

class _BytesResponse(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb):
        self.close(); return False

def _zip_csv(name, text):
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(name, text)
    return out.getvalue()

def _bootstrap_zip():
    text = BOOT.read_text()
    lines = [x for x in text.splitlines() if x.strip()]
    if len(lines) != 24 or not lines[1].startswith("1567900800000,") or not lines[-1].startswith("1569801600000,"):
        raise RuntimeError("persisted launch-era bootstrap integrity gate failed")
    return _zip_csv("BTCUSDT-1d-2019-09.csv", text)

def _daily_month_zip(year, month):
    pieces=[]
    header=None
    ndays=calendar.monthrange(year, month)[1]
    for day in range(1, ndays+1):
        ds=f"{year:04d}-{month:02d}-{day:02d}"
        url=f"https://data.binance.vision/data/futures/um/daily/klines/BTCUSDT/1d/BTCUSDT-1d-{ds}.zip"
        try:
            with ORIG_URLOPEN(url, timeout=60) as r: b=r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404: continue
            raise
        with zipfile.ZipFile(io.BytesIO(b)) as z:
            names=[n for n in z.namelist() if n.endswith('.csv')]
            if not names: raise RuntimeError(f"daily Vision ZIP has no CSV: {url}")
            lines=z.read(names[0]).decode('utf-8').splitlines()
        if not lines: continue
        if not lines[0].split(',')[0].isdigit():
            if header is None: header=lines[0]
            lines=lines[1:]
        pieces.extend(x for x in lines if x.strip())
    if not pieces:
        raise RuntimeError(f"no daily Vision rows available for missing monthly object {year:04d}-{month:02d}")
    text=((header+'\n') if header else '')+'\n'.join(pieces)+'\n'
    return _zip_csv(f"BTCUSDT-1d-{year:04d}-{month:02d}.csv", text)

def patched_urlopen(url, *args, **kwargs):
    target = url.full_url if hasattr(url, "full_url") else str(url)
    if target == SEP2019:
        return _BytesResponse(_bootstrap_zip())
    m=MONTH_RE.match(target)
    if m:
        try:
            return ORIG_URLOPEN(url, *args, **kwargs)
        except urllib.error.HTTPError as e:
            if e.code != 404: raise
            return _BytesResponse(_daily_month_zip(int(m.group(1)), int(m.group(2))))
    return ORIG_URLOPEN(url, *args, **kwargs)

urllib.request.urlopen = patched_urlopen
runpy.run_path("research/broad_cycle1/run_cycle1.py", run_name="__main__")

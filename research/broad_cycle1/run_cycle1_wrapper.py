#!/usr/bin/env python3
"""Data-engineering bridge for the frozen Cycle-1 runner.

Binance Vision has no monthly USD-M BTCUSDT 1d archive object for 2019-09.
The official connected Binance USD-M endpoint was used outside the runner to
retrieve and audit the 2019-09-08..2019-09-30 rows; those rows are persisted
verbatim in bootstrap_btcusdt_um_1d_2019-09.csv. This wrapper intercepts only
the missing Vision object and serves that frozen bootstrap as an in-memory ZIP.
Candidate/performance rules in run_cycle1.py are untouched.
"""
import io
import runpy
import urllib.request
import zipfile
from pathlib import Path

ORIG_URLOPEN = urllib.request.urlopen
MISSING = "https://data.binance.vision/data/futures/um/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2019-09.zip"
BOOT = Path("research/broad_cycle1/bootstrap_btcusdt_um_1d_2019-09.csv")

class _BytesResponse(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb):
        self.close(); return False

def _bootstrap_zip():
    text = BOOT.read_text()
    lines = [x for x in text.splitlines() if x.strip()]
    if len(lines) != 24 or not lines[1].startswith("1567900800000,") or not lines[-1].startswith("1569801600000,"):
        raise RuntimeError("persisted launch-era bootstrap integrity gate failed")
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("BTCUSDT-1d-2019-09.csv", text)
    return out.getvalue()

def patched_urlopen(url, *args, **kwargs):
    target = url.full_url if hasattr(url, "full_url") else str(url)
    if target == MISSING:
        return _BytesResponse(_bootstrap_zip())
    return ORIG_URLOPEN(url, *args, **kwargs)

urllib.request.urlopen = patched_urlopen
runpy.run_path("research/broad_cycle1/run_cycle1.py", run_name="__main__")

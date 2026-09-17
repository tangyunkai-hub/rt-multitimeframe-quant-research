#!/usr/bin/env python3
"""Data-engineering bridge for the frozen Cycle-1 runner.

Binance Vision has no monthly USD-M BTCUSDT 1d archive object for 2019-09,
while the official USD-M futures kline API returns the launch-era daily bars.
This wrapper intercepts only that missing archive request, obtains the same
12-column kline schema from the official futures API, wraps it in an in-memory
ZIP, and leaves every candidate/performance rule in run_cycle1.py unchanged.
"""
import csv
import io
import json
import runpy
import urllib.parse
import urllib.request
import zipfile

ORIG_URLOPEN = urllib.request.urlopen
MISSING = "https://data.binance.vision/data/futures/um/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2019-09.zip"
API = "https://fapi.binance.com/fapi/v1/klines"
START = 1567900800000  # 2019-09-08 00:00 UTC
END = 1569887999999    # 2019-09-30 23:59:59.999 UTC

class _BytesResponse(io.BytesIO):
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

def _synth_sep2019_zip(timeout=60):
    qs = urllib.parse.urlencode({
        "symbol": "BTCUSDT", "interval": "1d", "startTime": START,
        "endTime": END, "limit": 100,
    })
    with ORIG_URLOPEN(API + "?" + qs, timeout=timeout) as r:
        payload = r.read()
    rows = json.loads(payload.decode("utf-8"))
    if not rows or int(rows[0][0]) != START or int(rows[-1][0]) != 1569801600000:
        raise RuntimeError("official futures API launch-era coverage mismatch")
    sio = io.StringIO()
    w = csv.writer(sio, lineterminator="\n")
    w.writerow(["open_time","open","high","low","close","volume","close_time","quote_volume","trades","taker_buy_base","taker_buy_quote","ignore"])
    w.writerows(rows)
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("BTCUSDT-1d-2019-09.csv", sio.getvalue())
    return out.getvalue()

def patched_urlopen(url, *args, **kwargs):
    target = url.full_url if hasattr(url, "full_url") else str(url)
    if target == MISSING:
        timeout = kwargs.get("timeout", args[1] if len(args) > 1 else 60)
        return _BytesResponse(_synth_sep2019_zip(timeout=timeout))
    return ORIG_URLOPEN(url, *args, **kwargs)

urllib.request.urlopen = patched_urlopen
runpy.run_path("research/broad_cycle1/run_cycle1.py", run_name="__main__")

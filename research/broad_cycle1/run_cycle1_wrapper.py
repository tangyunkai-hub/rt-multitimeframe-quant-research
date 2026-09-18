#!/usr/bin/env python3
"""Data-only bridge for frozen Cycle-1 runner; strategy code remains untouched."""
import calendar, io, re, runpy, urllib.error, urllib.request, zipfile
from pathlib import Path
ORIG_URLOPEN=urllib.request.urlopen
MONTH_RE=re.compile(r"^https://data\.binance\.vision/data/futures/um/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-(\d{4})-(\d{2})\.zip$")
SEP=Path("research/broad_cycle1/bootstrap_btcusdt_um_1d_2019-09.csv")
Q4=Path("research/broad_cycle1/bootstrap_btcusdt_um_1d_2019-q4.csv")
class _BytesResponse(io.BytesIO):
 def __enter__(self): return self
 def __exit__(self,*a): self.close(); return False
def _zip(name,text):
 out=io.BytesIO()
 with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as z: z.writestr(name,text)
 return out.getvalue()
def _static_2019(month):
 p=SEP if month==9 else Q4
 lines=[x for x in p.read_text().splitlines() if x.strip()]
 header=lines[0] if not lines[0].split(',')[0].isdigit() else None
 data=lines[1:] if header else lines
 want=[]
 for x in data:
  ts=int(x.split(',')[0]); import datetime
  d=datetime.datetime.fromtimestamp(ts/1000,datetime.timezone.utc)
  if d.year==2019 and d.month==month: want.append(x)
 expected={9:23,10:31,11:30,12:31}[month]
 if len(want)!=expected: raise RuntimeError(f"2019-{month:02d} static bootstrap row gate {len(want)} != {expected}")
 text=((header+'\n') if header else '')+'\n'.join(want)+'\n'
 return _zip(f"BTCUSDT-1d-2019-{month:02d}.csv",text)
def _daily_month(year,month):
 pieces=[]; header=None
 for day in range(1,calendar.monthrange(year,month)[1]+1):
  ds=f"{year:04d}-{month:02d}-{day:02d}"; url=f"https://data.binance.vision/data/futures/um/daily/klines/BTCUSDT/1d/BTCUSDT-1d-{ds}.zip"
  try:
   with ORIG_URLOPEN(url,timeout=60) as r: b=r.read()
  except urllib.error.HTTPError as e:
   if e.code==404: continue
   raise
  with zipfile.ZipFile(io.BytesIO(b)) as z:
   names=[n for n in z.namelist() if n.endswith('.csv')]
   if not names: raise RuntimeError(f"daily ZIP has no CSV: {url}")
   ls=z.read(names[0]).decode().splitlines()
  if ls and not ls[0].split(',')[0].isdigit():
   if header is None: header=ls[0]
   ls=ls[1:]
  pieces += [x for x in ls if x.strip()]
 if not pieces: raise RuntimeError(f"no daily Vision rows for {year:04d}-{month:02d}")
 return _zip(f"BTCUSDT-1d-{year:04d}-{month:02d}.csv",((header+'\n') if header else '')+'\n'.join(pieces)+'\n')
def patched_urlopen(url,*args,**kwargs):
 target=url.full_url if hasattr(url,'full_url') else str(url); m=MONTH_RE.match(target)
 if m:
  y,mo=map(int,m.groups())
  if y==2019 and mo in (9,10,11,12): return _BytesResponse(_static_2019(mo))
  try: return ORIG_URLOPEN(url,*args,**kwargs)
  except urllib.error.HTTPError as e:
   if e.code!=404: raise
   return _BytesResponse(_daily_month(y,mo))
 return ORIG_URLOPEN(url,*args,**kwargs)
urllib.request.urlopen=patched_urlopen
runpy.run_path("research/broad_cycle1/run_cycle1.py",run_name="__main__")

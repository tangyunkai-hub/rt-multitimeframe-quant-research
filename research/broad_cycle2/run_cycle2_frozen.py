import csv, io, json, math, urllib.request, zipfile, calendar
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path("research/broad_cycle2")
SRC=ROOT/"source_freeze"
OUT=ROOT/"results"; OUT.mkdir(parents=True,exist_ok=True)
BASE="https://data.binance.vision/data/futures/um"
START_MS=1567900800000; END_MS=1789430400000
COSTS=[0.0007,0.0014,0.0028]

def getzip(url):
    with urllib.request.urlopen(url,timeout=60) as r: b=r.read()
    with zipfile.ZipFile(io.BytesIO(b)) as z:
        name=[n for n in z.namelist() if n.endswith(".csv")][0]
        return z.read(name).decode("utf-8")

def price_rows():
    rows=[]
    for y in range(2019,2027):
      for m in range(1,13):
        ym=f"{y:04d}-{m:02d}"
        if ym<"2019-09" or ym>"2026-08": continue
        try: txt=getzip(f"{BASE}/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-{ym}.zip")
        except Exception:
            if ym=="2019-09":
                txt=Path("research/broad_cycle1/bootstrap_btcusdt_um_1d_2019-09.csv").read_text()
            else: raise
        for r in csv.reader(io.StringIO(txt)):
            try: t=int(r[0])
            except: continue
            rows.append((t,float(r[1]),float(r[2]),float(r[3]),float(r[4])))
    for d in range(1,16):
        txt=getzip(f"{BASE}/daily/klines/BTCUSDT/1d/BTCUSDT-1d-2026-09-{d:02d}.zip")
        for r in csv.reader(io.StringIO(txt)):
            try: t=int(r[0])
            except: continue
            rows.append((t,float(r[1]),float(r[2]),float(r[3]),float(r[4])))
    by={r[0]:r for r in rows}; a=[by[k] for k in sorted(by) if START_MS<=k<=END_MS]
    assert a[0][0]==START_MS and a[-1][0]==END_MS and len(a)==2565
    assert all(a[i][0]-a[i-1][0]==86400000 for i in range(1,len(a)))
    return a

P=price_rows(); T=[r[0] for r in P]; O=[r[1] for r in P]; C=[r[4] for r in P]; n=len(P)
dates=[datetime.fromtimestamp(t/1000,tz=timezone.utc).date() for t in T]
idx={d:i for i,d in enumerate(dates)}
fund=json.loads((SRC/"btcusdt_usdm_funding_20190908_20260915.json").read_text())
prem=json.loads((SRC/"btcusdt_usdm_premium_1d_20190908_20260915.json").read_text())

fd={}
for r in fund:
    d=datetime.fromtimestamp(int(r["fundingTime"])/1000,tz=timezone.utc).date()
    fd[d]=fd.get(d,0.0)+float(r["fundingRate"])
pc={}
for r in prem:
    ms=int(r.get("openTime",r.get("open_time",r.get("timestamp",0))))
    d=datetime.fromtimestamp(ms/1000,tz=timezone.utc).date()
    val=r.get("close",r.get("premiumClose",r.get("premium_close")))
    pc[d]=float(val)

def rolling_calendar_sum(mapping,d,days):
    vals=[]
    for k in range(days):
        dd=d.fromordinal(d.toordinal()-k)
        if dd in mapping: vals.append(mapping[dd])
    return sum(vals) if vals else None

def sign(x): return 1.0 if x>0 else (-1.0 if x<0 else 0.0)
sig={k:[0.0]*n for k in ["F1","F2","F3","P1","P2","P3","V1","V2","V3","C1","C2","C3"]}
f30_hist=[]; p_hist=[]
lr=[None]+[math.log(C[i]/C[i-1]) for i in range(1,n)]
for i,d in enumerate(dates):
    f7=rolling_calendar_sum(fd,d,7); f30=rolling_calendar_sum(fd,d,30)
    if f7 is not None: sig["F1"][i]=-sign(f7)
    if f30 is not None:
        sig["F2"][i]=-sign(f30)
        if len(f30_hist)>=180:
            mu=sum(f30_hist)/len(f30_hist); sd=(sum((x-mu)**2 for x in f30_hist)/len(f30_hist))**0.5
            z=0 if sd==0 else (f30-mu)/sd
            sig["F3"][i]=-sign(z) if abs(z)>=1 else 0
        f30_hist.append(f30)
    if d in pc:
        x=pc[d]; sig["P1"][i]=-sign(x)
        vals=[pc[d.fromordinal(d.toordinal()-k)] for k in range(7) if d.fromordinal(d.toordinal()-k) in pc]
        if vals: sig["P2"][i]=-sign(sum(vals)/len(vals))
        if len(p_hist)>=180:
            mu=sum(p_hist)/len(p_hist); sd=(sum((v-mu)**2 for v in p_hist)/len(p_hist))**0.5
            z=0 if sd==0 else (x-mu)/sd
            sig["P3"][i]=-sign(z) if abs(z)>=1 else 0
        p_hist.append(x)
    if i>=60:
        def popsd(a):
            m=sum(a)/len(a); return (sum((x-m)**2 for x in a)/len(a))**0.5
        rv20=popsd(lr[i-19:i+1])*math.sqrt(365); rv60=popsd(lr[i-59:i+1])*math.sqrt(365)
        q=rv20/rv60 if rv60 else 1
        sig["V1"][i]=0 if q>1.25 else 1
        sig["V2"][i]=1 if q<0.80 else 0
        sig["V3"][i]=1 if q<0.80 else (-1 if q>1.25 else 0)
    if i+1<n:
        nd=dates[i+1]; wk=nd.weekday()
        sig["C1"][i]=0 if wk>=5 else 1
        sig["C2"][i]=1 if wk>=5 else 0
        last=calendar.monthrange(nd.year,nd.month)[1]
        sig["C3"][i]=1 if nd.day>=last-2 else 0

def maxdd(eq):
    p=eq[0]; m=0
    for x in eq: p=max(p,x); m=min(m,x/p-1)
    return m
def perf(s,cost):
    pos=[0.0]*n
    for j in range(1,n): pos[j]=s[j-1]
    ret=[0.0]*n; eq=[1.0]*n; turn=0
    for j in range(1,n):
        tr=abs(pos[j]-pos[j-1]); turn+=tr
        gross=pos[j]*(O[j+1]/O[j]-1) if j+1<n else 0
        ret[j]=gross-cost*tr; eq[j]=eq[j-1]*(1+ret[j])
    rr=ret[1:-1]; mu=sum(rr)/len(rr); sd=(sum((x-mu)**2 for x in rr)/(len(rr)-1))**0.5
    return ret,{"terminal_return":eq[-2]-1,"sharpe":mu/sd*math.sqrt(365) if sd else 0,"max_drawdown":maxdd(eq[:-1]),"turnover":turn,"exposure":sum(abs(x)>1e-12 for x in pos)/n}
def block(ret,lo,hi):
    x=1
    for i,r in enumerate(ret):
        if lo<=str(dates[i])<=hi: x*=1+r
    return x-1

eras=[("E1","2020-01-01","2021-12-31"),("E2","2022-01-01","2023-12-31"),("E3","2024-01-01","2026-09-15")]
out=[]
for name,s in sig.items():
    ret,b=perf(s,COSTS[0]); _,p28=perf(s,COSTS[1]); _,p56=perf(s,COSTS[2])
    er=[block(ret,a,z) for _,a,z in eras]
    yrs={str(y):block(ret,f"{y}-01-01",f"{y}-12-31") for y in range(2020,2027)}
    b.update({"candidate":name,"cost28_return":p28["terminal_return"],"cost56_return":p56["terminal_return"],"era_returns":er,"positive_eras":sum(x>0 for x in er),"worst_era":min(er),"year_returns":yrs,"worst_year":min(yrs.values())})
    out.append(b)
(OUT/"cycle2_results.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))

import csv,io,json,math,hashlib,urllib.request
from pathlib import Path
from datetime import date,timedelta
OUT=Path("artifacts/cycle2_v1_v1"); OUT.mkdir(parents=True,exist_ok=True)
URL="https://raw.githubusercontent.com/alessiostomeo/btc-cycle-data/main/bitstamp/1day/BTCUSD_bitstamp_daily_2012-2026.csv"
EXPECTED="3c8d32b1d13a8bf77348c9a04be616b7ba82b4a4553bfe59654260410c5a9e60"
with urllib.request.urlopen(URL,timeout=120) as r: raw=r.read()
rows=[]
for z in csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))):
 d=z["datetime_utc"][:10]
 if d<="2019-09-07": rows.append((d,*[float(z[k]) for k in ("open","high","low","close")],float(z.get("volume") or 0)))
rows.sort(); assert len(rows)==2807==len({r[0] for r in rows})
assert all(date.fromisoformat(b[0])-date.fromisoformat(a[0])==timedelta(days=1) for a,b in zip(rows,rows[1:]))
assert all(min(r[1:5])>0 and r[2]>=max(r[1],r[4]) and r[3]<=min(r[1],r[4]) for r in rows)
norm="date,open,high,low,close,volume\n"+"\n".join(",".join([r[0]]+[format(x,".12g") for x in r[1:]]) for r in rows)+"\n"
data_sha=hashlib.sha256(norm.encode()).hexdigest(); assert data_sha==EXPECTED
(OUT/"bitstamp_btcusd_daily_pre20190908.csv").write_text(norm)
O=[r[1] for r in rows]; C=[r[4] for r in rows]; n=len(rows)
lr=[None]+[math.log(C[i]/C[i-1]) for i in range(1,n)]
decision=[0.0]*n; ratio=[None]*n
for i in range(60,n):
 w20=lr[i-19:i+1]; w60=lr[i-59:i+1]
 m20=sum(w20)/20; m60=sum(w60)/60
 s20=(sum((x-m20)**2 for x in w20)/20)**0.5
 s60=(sum((x-m60)**2 for x in w60)/60)**0.5
 ratio[i]=s20/s60 if s60>0 else None
 decision[i]=0.0 if ratio[i] is not None and ratio[i]>1.25 else 1.0
def maxdd(eq):
 p=eq[0]; m=0
 for x in eq: p=max(p,x); m=min(m,x/p-1)
 return m
def perf(dec,cost):
 pos=[0.0]*n
 for j in range(1,n): pos[j]=dec[j-1]
 rr=[0.0]*n; eq=[1.0]*n; turn=0
 for j in range(1,n):
  t=abs(pos[j]-pos[j-1]); turn+=t
  gross=pos[j]*(O[j+1]/O[j]-1) if j+1<n else 0
  rr[j]=gross-cost*t; eq[j]=eq[j-1]*(1+rr[j])
 x=rr[1:-1]; mu=sum(x)/len(x); sd=(sum((v-mu)**2 for v in x)/(len(x)-1))**0.5
 return {"terminal_return":eq[-2]-1,"sharpe":mu/sd*math.sqrt(365) if sd else 0,"max_drawdown":maxdd(eq[:-1]),"turnover":turn,"invested_fraction":sum(abs(v)>1e-12 for v in pos)/n,"worst_daily_return":min(x)}
always=[1.0]*n
out={"V1":{},"ALWAYS_LONG":{}}
for name,dec in [("V1",decision),("ALWAYS_LONG",always)]:
 for tag,c in [("baseline",.0007),("stress28",.0014),("stress56",.0028)]: out[name][tag]=perf(dec,c)
out["incremental"]={"maxdd_improvement":out["V1"]["baseline"]["max_drawdown"]-out["ALWAYS_LONG"]["baseline"]["max_drawdown"],"sharpe_delta":out["V1"]["baseline"]["sharpe"]-out["ALWAYS_LONG"]["baseline"]["sharpe"],"terminal_return_delta":out["V1"]["baseline"]["terminal_return"]-out["ALWAYS_LONG"]["baseline"]["terminal_return"]}
meta={"data_sha256":data_sha,"runner_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),"rows":n,"first":rows[0][0],"last":rows[-1][0],"validated_alpha":False}
(OUT/"results.json").write_text(json.dumps(out,indent=2)); (OUT/"metadata.json").write_text(json.dumps(meta,indent=2))
print(json.dumps({"results":out,"meta":meta},indent=2))

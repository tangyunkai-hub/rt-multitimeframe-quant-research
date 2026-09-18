import csv, io, json, math, hashlib, urllib.request
from pathlib import Path
from datetime import datetime, timezone

OUT=Path('artifacts/broad_v1_pre2019'); OUT.mkdir(parents=True,exist_ok=True)
URL='https://raw.githubusercontent.com/alessiostomeo/btc-cycle-data/main/bitstamp/1day/BTCUSD_bitstamp_daily_2012-2026.csv'
CUTOFF='2019-09-07'
with urllib.request.urlopen(URL,timeout=120) as r: raw=r.read()
raw_sha=hashlib.sha256(raw).hexdigest(); text=raw.decode('utf-8-sig')
reader=csv.DictReader(io.StringIO(text)); rows=[]
for z in reader:
    ds=z['datetime_utc'][:10]
    if ds>CUTOFF: continue
    rows.append((ds,float(z['open']),float(z['high']),float(z['low']),float(z['close']),float(z.get('volume') or 0)))
rows.sort(key=lambda x:x[0]); assert rows
assert len(rows)==len({r[0] for r in rows})
nonpos=sum(not all(x>0 for x in r[1:5]) for r in rows)
bad=sum(not (r[2]>=max(r[1],r[3],r[4]) and r[3]<=min(r[1],r[2],r[4])) for r in rows)
from datetime import date,timedelta
gaps=[]
for a,b in zip(rows,rows[1:]):
    da=date.fromisoformat(a[0]); db=date.fromisoformat(b[0]);
    if db-da!=timedelta(days=1): gaps.append({'after':a[0],'before':b[0],'missing_days':(db-da).days-1})
assert nonpos==0 and bad==0 and not gaps
norm='date,open,high,low,close,volume\n'+'\n'.join(','.join([r[0]]+[format(x,'.12g') for x in r[1:]]) for r in rows)+'\n'
(OUT/'bitstamp_btcusd_daily_pre20190908.csv').write_text(norm)
norm_sha=hashlib.sha256(norm.encode()).hexdigest()
manifest={'source_url':URL,'source_repo':'alessiostomeo/btc-cycle-data','source_path':'bitstamp/1day/BTCUSD_bitstamp_daily_2012-2026.csv','source_role':'durable source-faithful Bitstamp fallback under frozen addendum','raw_sha256':raw_sha,'normalized_sha256':norm_sha,'rows':len(rows),'first_date':rows[0][0],'last_date':rows[-1][0],'unique_dates':len(rows),'gap_count':len(gaps),'gaps':gaps,'nonpositive_ohlc':nonpos,'invalid_ohlc_envelope':bad,'performance_scope':'V1_INDEPENDENT_TIME_BTC_SPOT'}
(OUT/'source_manifest.json').write_text(json.dumps(manifest,indent=2))
O=[r[1] for r in rows]; C=[r[4] for r in rows]; n=len(rows)
def tsmom(N):
 s=[0.0]*n
 for i in range(N,n): s[i]=1 if C[i]>C[i-N] else (-1 if C[i]<C[i-N] else 0)
 return s
def vm(base):
 out=[0.0]*n; lr=[None]+[math.log(C[i]/C[i-1]) for i in range(1,n)]
 for i in range(20,n):
  w=lr[i-19:i+1]
  if any(x is None for x in w): continue
  mu=sum(w)/20; sd=(sum((x-mu)**2 for x in w)/19)**0.5; vol=sd*math.sqrt(365); lev=0 if vol<=0 else min(2,0.20/vol); out[i]=base[i]*lev
 return out
def maxdd(eq):
 peak=eq[0]; m=0
 for x in eq: peak=max(peak,x); m=min(m,x/peak-1)
 return m
def perf(decision,cost):
 pos=[0.0]*n
 for j in range(1,n): pos[j]=decision[j-1]
 rets=[0.0]*n; eq=[1.0]*n; turns=0
 for j in range(1,n):
  turnover=abs(pos[j]-pos[j-1]); turns+=turnover
  gross=pos[j]*(O[j+1]/O[j]-1) if j+1<n else 0.0
  rets[j]=gross-cost*turnover; eq[j]=eq[j-1]*(1+rets[j])
 rr=rets[1:-1]; mu=sum(rr)/len(rr); sd=(sum((x-mu)**2 for x in rr)/(len(rr)-1))**0.5
 return {'terminal_return':eq[-2]-1,'sharpe':mu/sd*math.sqrt(365) if sd else 0,'max_drawdown':maxdd(eq[:-1]),'turnover_notional':turns,'active_fraction':sum(abs(x)>1e-12 for x in pos)/n}
b20=tsmom(20); candidates={'TSMOM_120':tsmom(120),'VM_TSMOM20':vm(b20)}
results=[]
for name,s in candidates.items():
 p=perf(s,.0007); p28=perf(s,.0014); p56=perf(s,.0028); p.update({'candidate':name,'return_cost28bp_rt':p28['terminal_return'],'return_cost56bp_rt':p56['terminal_return']}); results.append(p)
(OUT/'v1_results.json').write_text(json.dumps(results,indent=2))
with (OUT/'v1_results.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['candidate','terminal_return','sharpe','max_drawdown','turnover_notional','active_fraction','return_cost28bp_rt','return_cost56bp_rt']); w.writeheader(); w.writerows(results)
meta={'data_sha256':norm_sha,'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'candidate_count':2,'candidate_names':['TSMOM_120','VM_TSMOM20'],'validated_alpha':False,'freeze_addendum':'research/broad_cycle1/V1_PRE2019_SOURCE_ADDENDUM_20260918.md'}
(OUT/'run_metadata.json').write_text(json.dumps(meta,indent=2))
print(json.dumps({'manifest':manifest,'results':results,'meta':meta},indent=2))

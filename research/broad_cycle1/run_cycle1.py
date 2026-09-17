import csv, io, json, math, hashlib, urllib.request, zipfile
from pathlib import Path
from datetime import date, timedelta

OUT=Path('artifacts/broad_cycle1'); OUT.mkdir(parents=True,exist_ok=True)
BASE='https://data.binance.vision/data/futures/um'
CUTOFF='2026-09-15'

def getzip(url):
    with urllib.request.urlopen(url, timeout=60) as r: b=r.read()
    with zipfile.ZipFile(io.BytesIO(b)) as z:
        names=[n for n in z.namelist() if n.endswith('.csv')]
        return z.read(names[0]).decode('utf-8')

def parse(text):
    rows=[]
    for row in csv.reader(io.StringIO(text)):
        if not row: continue
        try: ot=int(row[0])
        except: continue
        rows.append((ot,float(row[1]),float(row[2]),float(row[3]),float(row[4]),float(row[5])))
    return rows

rows=[]; sources=[]
for y in range(2019,2027):
  for m in range(1,13):
    ym=f'{y:04d}-{m:02d}'
    if ym<'2019-09' or ym>'2026-08': continue
    url=f'{BASE}/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-{ym}.zip'
    try:
      txt=getzip(url); rr=parse(txt); rows+=rr; sources.append({'url':url,'rows':len(rr),'sha256':hashlib.sha256(txt.encode()).hexdigest()})
    except Exception as e: raise RuntimeError(f'failed {url}: {e}')
for d in range(1,16):
    ds=f'2026-09-{d:02d}'; url=f'{BASE}/daily/klines/BTCUSDT/1d/BTCUSDT-1d-{ds}.zip'
    txt=getzip(url); rr=parse(txt); rows+=rr; sources.append({'url':url,'rows':len(rr),'sha256':hashlib.sha256(txt.encode()).hexdigest()})

by={r[0]:r for r in rows}; rows=[by[k] for k in sorted(by)]
# cutoff and launch
cutoff_ms=1789430400000
rows=[r for r in rows if 1567900800000<=r[0]<=cutoff_ms]
assert rows and rows[0][0]==1567900800000 and rows[-1][0]==cutoff_ms
assert len(rows)==len({r[0] for r in rows})
assert all(rows[i][0]-rows[i-1][0]==86400000 for i in range(1,len(rows)))
assert all(r[1]>0 and r[2]>0 and r[3]>0 and r[4]>0 and r[2]>=max(r[1],r[3],r[4]) and r[3]<=min(r[1],r[2],r[4]) for r in rows)

norm='open_time,open,high,low,close,volume\n'+'\n'.join(','.join([str(r[0])]+[format(x,'.12g') for x in r[1:]]) for r in rows)+'\n'
(OUT/'btcusdt_um_1d_20190908_20260915.csv').write_text(norm)
data_sha=hashlib.sha256(norm.encode()).hexdigest()
manifest={'dataset':'Binance BTCUSDT USD-M perpetual 1d','start':'2019-09-08','end':CUTOFF,'rows':len(rows),'unique_open_time':len(rows),'gap_count':0,'ohlc_envelope_invalid':0,'nonpositive_ohlc':0,'normalized_sha256':data_sha,'sources':sources}
(OUT/'source_manifest.json').write_text(json.dumps(manifest,indent=2))

O=[r[1] for r in rows]; H=[r[2] for r in rows]; L=[r[3] for r in rows]; C=[r[4] for r in rows]; T=[r[0] for r in rows]; n=len(rows)

def rsi_wilder(c,period=14):
    out=[None]*len(c); gains=[]; losses=[]
    for i in range(1,period+1):
        d=c[i]-c[i-1]; gains.append(max(d,0)); losses.append(max(-d,0))
    ag=sum(gains)/period; al=sum(losses)/period
    def val(ag,al): return 100.0 if al==0 else 100-100/(1+ag/al)
    out[period]=val(ag,al)
    for i in range(period+1,len(c)):
        d=c[i]-c[i-1]; g=max(d,0); l=max(-d,0); ag=(ag*(period-1)+g)/period; al=(al*(period-1)+l)/period; out[i]=val(ag,al)
    return out
RSI=rsi_wilder(C)

def base_targets(kind,param=None):
    s=[0.0]*n
    if kind=='tsmom':
      N=param
      for i in range(N,n): s[i]=1 if C[i]>C[i-N] else (-1 if C[i]<C[i-N] else 0)
    elif kind=='donchian':
      ent,ex=param; state=0
      for i in range(n):
        if i<max(ent,ex): s[i]=state; continue
        long_ent=C[i]>max(H[i-ent:i]); short_ent=C[i]<min(L[i-ent:i])
        if state==0:
          if long_ent: state=1
          elif short_ent: state=-1
        elif state==1:
          if short_ent: state=-1
          elif C[i]<min(L[i-ex:i]): state=0
        else:
          if long_ent: state=1
          elif C[i]>max(H[i-ex:i]): state=0
        s[i]=state
    elif kind=='z':
      th=param; state=0
      for i in range(19,n):
        w=C[i-19:i+1]; mu=sum(w)/20; sd=(sum((x-mu)**2 for x in w)/20)**0.5; z=0 if sd==0 else (C[i]-mu)/sd
        if state==0:
          if z>th: state=-1
          elif z<-th: state=1
        elif state==1:
          if z>=th: state=-1
          elif z>=0: state=0
        else:
          if z<=-th: state=1
          elif z<=0: state=0
        s[i]=state
    elif kind=='rsi':
      state=0
      for i in range(n):
        x=RSI[i]
        if x is None: s[i]=state; continue
        if state==0:
          if x<30: state=1
          elif x>70: state=-1
        elif state==1:
          if x>70: state=-1
          elif x>=50: state=0
        else:
          if x<30: state=1
          elif x<=50: state=0
        s[i]=state
    return s

def vm(base):
    out=[0.0]*n
    lr=[None]+[math.log(C[i]/C[i-1]) for i in range(1,n)]
    for i in range(20,n):
      w=lr[i-19:i+1]; mu=sum(w)/20; sd=(sum((x-mu)**2 for x in w)/19)**0.5; vol=sd*math.sqrt(365); lev=0 if vol<=0 else min(2,0.20/vol); out[i]=base[i]*lev
    return out

def maxdd(eq):
    peak=eq[0]; m=0
    for x in eq: peak=max(peak,x); m=min(m,x/peak-1)
    return m

def perf(decision,cost_side):
    # decision at close i applies from open i+1. position[j]=decision[j-1]
    pos=[0.0]*n
    for j in range(1,n): pos[j]=decision[j-1]
    rets=[0.0]*n; eq=[1.0]*n; turns=0
    for j in range(1,n):
      turnover=abs(pos[j]-pos[j-1]); turns+=turnover
      gross=pos[j]*(O[j+1]/O[j]-1) if j+1<n else 0.0
      rets[j]=gross-cost_side*turnover
      eq[j]=eq[j-1]*(1+rets[j])
    rr=rets[1:-1]; mu=sum(rr)/len(rr); sd=(sum((x-mu)**2 for x in rr)/(len(rr)-1))**0.5
    sharpe=mu/sd*math.sqrt(365) if sd else 0
    return {'terminal_return':eq[-2]-1,'sharpe':sharpe,'max_drawdown':maxdd(eq[:-1]),'turnover_notional':turns,'active_fraction':sum(abs(x)>1e-12 for x in pos)/n,'daily_returns':rets,'equity':eq}

bases={
'TSMOM_20':base_targets('tsmom',20),'TSMOM_60':base_targets('tsmom',60),'TSMOM_120':base_targets('tsmom',120),
'DONCHIAN_20':base_targets('donchian',(20,10)),'DONCHIAN_55':base_targets('donchian',(55,20)),'DONCHIAN_120':base_targets('donchian',(120,40)),
'MR_Z20_1':base_targets('z',1),'MR_Z20_2':base_targets('z',2),'MR_RSI14':base_targets('rsi')}
bases['VM_TSMOM20']=vm(bases['TSMOM_20']); bases['VM_TSMOM60']=vm(bases['TSMOM_60']); bases['VM_DONCHIAN55']=vm(bases['DONCHIAN_55'])

def dt(ms):
 import datetime
 return datetime.datetime.utcfromtimestamp(ms/1000).strftime('%Y-%m-%d')

def block_return(rets,lo,hi):
    x=1.0
    for i,r in enumerate(rets):
      d=dt(T[i])
      if lo<=d<=hi: x*=1+r
    return x-1

results=[]; diagnostics=[]
for name,sig in bases.items():
  p=perf(sig,.0007)
  p28=perf(sig,.0014); p56=perf(sig,.0028)
  rec={k:p[k] for k in ['terminal_return','sharpe','max_drawdown','turnover_notional','active_fraction']}; rec.update({'candidate':name,'return_cost28bp_rt':p28['terminal_return'],'return_cost56bp_rt':p56['terminal_return']})
  eras=[('ERA1','2019-09-08','2021-12-31'),('ERA2','2022-01-01','2023-12-31'),('ERA3','2024-01-01',CUTOFF)]
  er=[]
  for label,lo,hi in eras:
    br=block_return(p['daily_returns'],lo,hi); er.append(br); diagnostics.append({'candidate':name,'block':label,'start':lo,'end':hi,'return':br})
  for y in range(2019,2027):
    lo=f'{y}-01-01'; hi=f'{y}-12-31'; diagnostics.append({'candidate':name,'block':str(y),'start':lo,'end':hi,'return':block_return(p['daily_returns'],lo,hi)})
  rec['positive_eras']=sum(x>0 for x in er); rec['worst_era_return']=min(er); rec['era_returns']=er
  results.append(rec)

results.sort(key=lambda x:(x['positive_eras'],x['worst_era_return'],x['max_drawdown'],x['return_cost56bp_rt'],x['terminal_return']),reverse=True)
(OUT/'cycle1_results.json').write_text(json.dumps(results,indent=2))
with (OUT/'cycle1_results.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['candidate','terminal_return','sharpe','max_drawdown','turnover_notional','active_fraction','return_cost28bp_rt','return_cost56bp_rt','positive_eras','worst_era_return','era_returns']); w.writeheader(); w.writerows(results)
with (OUT/'cycle1_diagnostics.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['candidate','block','start','end','return']); w.writeheader(); w.writerows(diagnostics)
runmeta={'data_sha256':data_sha,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'candidate_count':12,'baseline_cost_side':0.0007,'stress_cost_side':[0.0014,0.0028],'performance_scope':'CONSUMED_DEVELOPMENT_ONLY','validated_alpha':False}
(OUT/'run_metadata.json').write_text(json.dumps(runmeta,indent=2))
print(json.dumps({'manifest':manifest,'results':results,'run_metadata':runmeta},indent=2))
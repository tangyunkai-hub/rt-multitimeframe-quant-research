from __future__ import annotations

import argparse, hashlib, io, json, urllib.request, zipfile
from pathlib import Path
import pandas as pd

BASE='https://data.binance.vision/data/spot/monthly/klines'
COLS=['open_time_ms','open','high','low','close','volume','close_time_ms','quote_asset_volume','number_of_trades','taker_buy_base_asset_volume','taker_buy_quote_asset_volume','ignore']
TFSEC={'2h':7200,'8h':28800,'3d':259200}


def sha(b): return hashlib.sha256(b).hexdigest()
def parse_utc(s): return pd.to_datetime(s,format='mixed',utc=True)

def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'rtquant-external-validation/1.0'})
    with urllib.request.urlopen(req,timeout=60) as r: return r.read()

def checksum(text): return text.strip().split()[0].lower()

def read_zip(blob):
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        names=[n for n in z.namelist() if n.lower().endswith('.csv')]
        if len(names)!=1: raise ValueError(names)
        d=pd.read_csv(io.BytesIO(z.read(names[0])),header=None,names=COLS)
    for c in ['open_time_ms','close_time_ms','number_of_trades']: d[c]=pd.to_numeric(d[c],errors='raise').astype('int64')
    for c in ['open','high','low','close','volume']: d[c]=pd.to_numeric(d[c],errors='raise').astype(float)
    d['open_time']=pd.to_datetime(d.open_time_ms,unit='ms',utc=True)
    return d

def load_norm(p):
    d=pd.read_csv(p); d['open_time']=parse_utc(d.open_time); d['availability_time']=parse_utc(d.availability_time)
    for c in ['open','high','low','close','volume']: d[c]=pd.to_numeric(d[c],errors='raise').astype(float)
    return d.sort_values('open_time').drop_duplicates('open_time',keep='last').reset_index(drop=True)

def download_1m(symbol,month,cache,manifest):
    cache.mkdir(parents=True,exist_ok=True); p=cache/f'{symbol}_1m_{month}.csv.gz'
    if p.exists():
        d=pd.read_csv(p); d['open_time']=parse_utc(d.open_time); return d
    name=f'{symbol}-1m-{month}.zip'; url=f'{BASE}/{symbol}/1m/{name}'
    blob=get(url); local=sha(blob); remote=checksum(get(url+'.CHECKSUM').decode())
    if local!=remote: raise RuntimeError(f'1m checksum mismatch {symbol} {month}')
    d=read_zip(blob)[['open_time','open','high','low','close','volume','number_of_trades']]
    d.to_csv(p,index=False,compression='gzip')
    manifest.append({'symbol':symbol,'month':month,'url':url,'checksum_url':url+'.CHECKSUM','sha256':local,'rows':len(d)})
    return d

def one_minute_to_15m(d):
    x=d.set_index(parse_utc(d.open_time)).sort_index()
    cnt=x.close.resample('15min',label='left',closed='left',origin='epoch').count().rename('one_minute_count')
    r=x[['open','high','low','close','volume']].resample('15min',label='left',closed='left',origin='epoch').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).join(cnt)
    return r[r.one_minute_count.eq(15)].copy()

def aggregate_15m(d15,tf):
    x=d15.set_index(parse_utc(d15.open_time)).sort_index()
    step=pd.Timedelta(seconds=TFSEC[tf])
    xa=x.copy(); xa.index=xa.index+pd.Timedelta(minutes=15)
    return xa[['open','high','low','close','volume']].resample(step,label='right',closed='right',origin='epoch').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna(subset=['open','high','low','close'])

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='external_history_2017_2022'); a=ap.parse_args(); root=Path(a.root)
    detp=root/'binance_parity_mismatch_details.csv'
    if not detp.exists(): raise SystemExit('missing parity mismatch details')
    det=pd.read_csv(detp)
    if det.empty:
        (root/'ONE_MINUTE_RECONCILIATION.json').write_text(json.dumps({'status':'NOT_NEEDED'},indent=2)); return
    det['availability_time']=parse_utc(det.availability_time)
    source=[]; patch_rows=[]; result=[]
    for symbol in sorted(det.symbol.unique()):
        original=load_norm(root/'binance'/f'{symbol}_15m_2017-2022.csv.gz')
        reconciled=original.copy().set_index('open_time')
        sym=det[det.symbol.eq(symbol)].copy()
        months=set()
        for _,r in sym.iterrows():
            end=r.availability_time; start=end-pd.Timedelta(seconds=TFSEC[r.interval])
            for t in [start,end-pd.Timedelta(nanoseconds=1)]: months.add(t.strftime('%Y-%m'))
        one=[]
        for m in sorted(months): one.append(download_1m(symbol,m,root/'one_minute_cache',source))
        d1=pd.concat(one,ignore_index=True).sort_values('open_time').drop_duplicates('open_time')
        r15=one_minute_to_15m(d1)
        affected=set()
        for _,r in sym.iterrows():
            end=r.availability_time; start=end-pd.Timedelta(seconds=TFSEC[r.interval])
            affected.update(r15.index[(r15.index>=start)&(r15.index<end)].tolist())
        for t in sorted(affected):
            if t not in r15.index: continue
            new=r15.loc[t]; old=reconciled.loc[t] if t in reconciled.index else None
            oldvals=None if old is None else [float(old[c]) for c in ['open','high','low','close','volume']]
            newvals=[float(new[c]) for c in ['open','high','low','close','volume']]
            if oldvals is None or any(abs(x-y)>1e-10 for x,y in zip(oldvals,newvals)):
                reconciled.loc[t,['open','high','low','close','volume']]=newvals
                if 'availability_time' in reconciled.columns: reconciled.loc[t,'availability_time']=t+pd.Timedelta(minutes=15)
                if 'number_of_trades' in reconciled.columns and old is None: reconciled.loc[t,'number_of_trades']=pd.NA
                patch_rows.append({'symbol':symbol,'open_time':t,'action':'add' if old is None else 'replace','old_values':oldvals,'new_values':newvals,'source':'official Binance 1m x15'})
        rec=reconciled.reset_index().sort_values('open_time')
        accepted=True
        for tf in ['2h','8h','3d']:
            q=sym[sym.interval.eq(tf)]
            if q.empty: continue
            native=load_norm(root/'binance'/f'{symbol}_{tf}_2017-2022.csv.gz').set_index('availability_time')
            agg=aggregate_15m(rec,tf)
            for _,r in q.iterrows():
                t=r.availability_time
                if t not in agg.index or t not in native.index:
                    result.append({'symbol':symbol,'interval':tf,'availability_time':str(t),'status':'MISSING_AFTER_RECONCILIATION'}); accepted=False; continue
                diffs={c:abs(float(agg.at[t,c])-float(native.at[t,c])) for c in ['open','high','low','close']}
                ok=max(diffs.values())<=1e-8
                result.append({'symbol':symbol,'interval':tf,'availability_time':str(t),'status':'MATCH' if ok else 'STILL_MISMATCH',**{f'absdiff_{k}':v for k,v in diffs.items()}})
                accepted &= ok
        out=root/'binance'/f'{symbol}_15m_2017-2022_reconciled_from_official_1m.csv.gz'
        if accepted: rec.to_csv(out,index=False,compression='gzip')
        elif out.exists(): out.unlink()
    pd.DataFrame(source).to_csv(root/'binance_1m_reconciliation_source_manifest.csv',index=False)
    pd.DataFrame(patch_rows).to_csv(root/'binance_15m_reconciliation_patch_manifest.csv',index=False)
    pd.DataFrame(result).to_csv(root/'binance_1m_reconciliation_results.csv',index=False)
    all_ok=bool(result) and all(x['status']=='MATCH' for x in result)
    summary={'status':'PASS' if all_ok else 'FAIL','patch_count':len(patch_rows),'mismatch_bins_checked':len(result),'rule':'Only official Binance 1m x15 reconstruction; no interpolation or synthetic prices; original 15m archives remain unchanged.'}
    (root/'ONE_MINUTE_RECONCILIATION.json').write_text(json.dumps(summary,indent=2)); print(json.dumps(summary,indent=2))
    if not all_ok: raise SystemExit('official 1m reconciliation did not resolve every native higher-TF mismatch')

if __name__=='__main__': main()

from __future__ import annotations

import argparse, hashlib, io, json, urllib.error, urllib.request, zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import pandas as pd

MONTHLY = 'https://data.binance.vision/data/spot/monthly/klines'
DAILY = 'https://data.binance.vision/data/spot/daily/klines'
COLS = ['open_time_ms','open','high','low','close','volume','close_time_ms','quote_asset_volume','number_of_trades','taker_buy_base_asset_volume','taker_buy_quote_asset_volume','ignore']
TFSEC = {'30m':1800,'1h':3600,'2h':7200,'4h':14400,'8h':28800,'12h':43200,'1d':86400,'3d':259200,'1w':604800}
INTERVALS = list(TFSEC)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={'User-Agent':'rtquant-native-regression/1.0'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def checksum(text: str) -> str:
    return text.strip().splitlines()[0].replace('*',' ').split()[0].lower()


def read_zip(blob: bytes) -> pd.DataFrame:
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        names=[n for n in z.namelist() if n.lower().endswith('.csv')]
        if len(names)!=1:
            raise ValueError(f'expected one csv, got {names}')
        d=pd.read_csv(io.BytesIO(z.read(names[0])),header=None,names=COLS)
    for c in ['open_time_ms','close_time_ms','number_of_trades']:
        d[c]=pd.to_numeric(d[c],errors='raise').astype('int64')
    for c in ['open','high','low','close','volume']:
        d[c]=pd.to_numeric(d[c],errors='raise').astype(float)
    return d


def verified_archive(url: str):
    blob=get(url)
    local=sha(blob)
    remote=checksum(get(url+'.CHECKSUM').decode('utf-8','replace'))
    if local!=remote:
        raise RuntimeError(f'checksum mismatch: {url}')
    return read_zip(blob), local


def month_iter(start_ym: str, end_ym: str):
    y,m=map(int,start_ym.split('-')); ey,em=map(int,end_ym.split('-'))
    while (y,m)<=(ey,em):
        yield f'{y:04d}-{m:02d}'
        m+=1
        if m==13: y+=1; m=1


def day_iter(start_day: str, end_day: str):
    d=date.fromisoformat(start_day); e=date.fromisoformat(end_day)
    while d<=e:
        yield d.isoformat(); d+=timedelta(days=1)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--out',default='modern_native_regression_v2')
    ap.add_argument('--monthly-start',default='2023-06')
    ap.add_argument('--monthly-end',default='2026-08')
    ap.add_argument('--daily-start',default='2026-09-01')
    ap.add_argument('--daily-end',default='2026-09-11')
    a=ap.parse_args(); out=Path(a.out); (out/'binance').mkdir(parents=True,exist_ok=True)
    manifest=[]; audits=[]
    for tf in INTERVALS:
        frames=[]
        for ym in month_iter(a.monthly_start,a.monthly_end):
            name=f'BTCUSDT-{tf}-{ym}.zip'; url=f'{MONTHLY}/BTCUSDT/{tf}/{name}'
            d,h=verified_archive(url); frames.append(d)
            manifest.append({'source':'monthly','interval':tf,'period':ym,'url':url,'sha256':h,'rows':len(d),'status':'ok'})
        for ds in day_iter(a.daily_start,a.daily_end):
            name=f'BTCUSDT-{tf}-{ds}.zip'; url=f'{DAILY}/BTCUSDT/{tf}/{name}'
            try:
                d,h=verified_archive(url)
            except urllib.error.HTTPError as e:
                if e.code==404:
                    manifest.append({'source':'daily','interval':tf,'period':ds,'url':url,'sha256':None,'rows':0,'status':'404_no_bar_open_on_day'})
                    continue
                raise
            frames.append(d); manifest.append({'source':'daily','interval':tf,'period':ds,'url':url,'sha256':h,'rows':len(d),'status':'ok'})
        d=pd.concat(frames,ignore_index=True).sort_values('open_time_ms').drop_duplicates('open_time_ms',keep='last').reset_index(drop=True)
        d['open_time']=pd.to_datetime(d.open_time_ms,unit='ms',utc=True)
        d['availability_time']=d.open_time+pd.to_timedelta(TFSEC[tf],unit='s')
        q=d[['open_time','availability_time','open','high','low','close','volume','number_of_trades']]
        p=out/'binance'/f'BTCUSDT_{tf}_2023-06_to_2026-09-11.csv.gz'; q.to_csv(p,index=False,compression='gzip')
        t=q.open_time; env=((q.high<q[['open','close','low']].max(axis=1))|(q.low>q[['open','close','high']].min(axis=1)))
        audits.append({'interval':tf,'rows':len(q),'start':str(t.iloc[0]),'end':str(t.iloc[-1]),'duplicate_timestamps':int(t.duplicated().sum()),'monotonic':bool(t.is_monotonic_increasing),'ohlc_envelope_failures':int(env.sum()),'normalized_sha256':sha(p.read_bytes())})
        print(tf,len(q),t.iloc[0],t.iloc[-1],flush=True)
    pd.DataFrame(manifest).to_csv(out/'source_manifest.csv',index=False)
    ad=pd.DataFrame(audits); ad.to_csv(out/'integrity.csv',index=False)
    bad=ad[(ad.duplicate_timestamps!=0)|(~ad.monotonic)|(ad.ohlc_envelope_failures!=0)]
    summary={'status':'PASS' if bad.empty else 'FAIL','purpose':'MODERN_SAMPLE_NATIVE_ADAPTER_REGRESSION_DATA_ONLY','performance_evaluation_allowed':False,'intervals':INTERVALS,'failed_series':int(len(bad)),'generated_at_utc':datetime.now(timezone.utc).isoformat()}
    (out/'DATA_GATE.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2),flush=True)
    if not bad.empty: raise SystemExit('modern native data integrity failed')

if __name__=='__main__': main()

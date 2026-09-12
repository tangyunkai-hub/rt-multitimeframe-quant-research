from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd

TFSEC={"15m":900,"2h":7200,"8h":28800,"3d":259200}
EXPECTED={"2h":8,"8h":32,"3d":288}

def parse_utc(s):
    # Old Binance archives include a few non-canonical sub-second timestamps after maintenance events.
    # pandas 3 requires explicit mixed ISO parsing for these legitimate source rows.
    return pd.to_datetime(s,format='mixed',utc=True)

def load(p):
    d=pd.read_csv(p)
    d['open_time']=parse_utc(d.open_time)
    d['availability_time']=parse_utc(d.availability_time)
    for c in ['open','high','low','close','volume']:
        d[c]=pd.to_numeric(d[c],errors='raise').astype(float)
    return d

def diagnose(root:Path,symbol:str,interval:str):
    base=load(root/'binance'/f'{symbol}_15m_2017-2022.csv.gz')
    native=load(root/'binance'/f'{symbol}_{interval}_2017-2022.csv.gz')
    b=base.set_index('availability_time').sort_index()
    n=native.set_index('availability_time').sort_index()
    freq=pd.Timedelta(seconds=TFSEC[interval])
    agg=b[['open','high','low','close','volume']].resample(freq,label='right',closed='right',origin='epoch').agg(
        {'open':'first','high':'max','low':'min','close':'last','volume':'sum'})
    cnt=b.close.resample(freq,label='right',closed='right',origin='epoch').count().rename('base_15m_count')
    r=agg.join(cnt).dropna(subset=['open','high','low','close'])
    common=r.index.intersection(n.index)
    cols=['open','high','low','close']
    diff=(r.loc[common,cols]-n.loc[common,cols]).abs()
    mm=(diff>1e-8).any(axis=1)
    rows=[]
    for t in common[mm]:
        rec={'symbol':symbol,'interval':interval,'availability_time':t,
             'base_15m_count':int(r.at[t,'base_15m_count']),'expected_15m_count':EXPECTED[interval],
             'incomplete_15m_bin':bool(r.at[t,'base_15m_count']!=EXPECTED[interval])}
        for c in cols:
            rec[f'resample_{c}']=float(r.at[t,c]); rec[f'native_{c}']=float(n.at[t,c]); rec[f'absdiff_{c}']=float(diff.at[t,c])
        rows.append(rec)
    return rows

def base_gaps(root:Path,symbol:str):
    d=load(root/'binance'/f'{symbol}_15m_2017-2022.csv.gz').sort_values('open_time')
    t=d.open_time.reset_index(drop=True); dt=t.diff(); expected=pd.Timedelta(minutes=15); rows=[]
    for i in dt[dt!=expected].dropna().index:
        missing=max(int(round(dt.iloc[i]/expected))-1,0)
        rows.append({'symbol':symbol,'previous_open_time':t.iloc[i-1],'next_open_time':t.iloc[i],
                     'gap_seconds':float(dt.iloc[i].total_seconds()),'estimated_missing_15m_bars':missing,
                     'next_open_time_on_15m_grid':bool((t.iloc[i].value//10**9)%900==0)})
    return rows

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='external_history_2017_2022'); a=ap.parse_args(); root=Path(a.root)
    details=[]; gaps=[]
    for s in ['BTCUSDT','ETHUSDT']:
        gaps+=base_gaps(root,s)
        for tf in ['2h','8h','3d']: details+=diagnose(root,s,tf)
    pd.DataFrame(details).to_csv(root/'binance_parity_mismatch_details.csv',index=False)
    pd.DataFrame(gaps).to_csv(root/'binance_15m_gap_details.csv',index=False)
    print(pd.DataFrame(details).to_string(index=False) if details else 'no parity mismatches')
    print('\n15m gaps:')
    print(pd.DataFrame(gaps).to_string(index=False) if gaps else 'no 15m gaps')

if __name__=='__main__': main()

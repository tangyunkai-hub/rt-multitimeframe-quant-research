import numpy as np
import pandas as pd

def _exp(s):
    return s.map({'CORE_LONG':1.0,'CORE_SHORT':-1.0,'FLAT':0.0}).astype(float)

def evaluate_paired_divergence(df: pd.DataFrame, *, round_trip_bps=14.0):
    req={'timestamp','close','A_core','B_core'}
    miss=req-set(df.columns)
    if miss: raise ValueError(f'missing columns: {sorted(miss)}')
    x=df.copy(); x['timestamp']=pd.to_datetime(x['timestamp'],utc=True); x=x.sort_values('timestamp').reset_index(drop=True)
    ret=x['close'].astype(float).pct_change().fillna(0.0); half=round_trip_bps/2/10000.0
    for side in ['A','B']:
        exp=_exp(x[f'{side}_core']); gross=exp.shift(1,fill_value=0)*ret
        turn=exp.diff().abs(); turn.iloc[0]=abs(exp.iloc[0])
        net=gross-turn*half
        x[f'{side}_lognet']=np.log1p(net)
    x['divergent']=x['A_core']!=x['B_core']
    starts=x['divergent'] & ~x['divergent'].shift(1,fill_value=False)
    segid=starts.cumsum().where(x['divergent'])
    rows=[]
    for sid,g in x[x['divergent']].groupby(segid.dropna()):
        a=float(g['A_lognet'].sum()); b=float(g['B_lognet'].sum())
        rows.append({'segment_id':int(sid),'start':g.timestamp.iloc[0],'end':g.timestamp.iloc[-1],
                     'A_log_return':a,'B_log_return':b,'paired_delta_log':b-a})
    seg=pd.DataFrame(rows)
    return {'segments':seg, 'total_paired_delta_log':float(seg.paired_delta_log.sum()) if len(seg) else 0.0}

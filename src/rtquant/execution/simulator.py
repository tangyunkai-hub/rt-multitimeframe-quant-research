import numpy as np
import pandas as pd

def simulate_next_open(df: pd.DataFrame, *, fee_bps_one_way=7.0, slippage_bps_one_way=0.0):
    req={'timestamp','open','close','target_exposure'}; miss=req-set(df.columns)
    if miss: raise ValueError(f'missing columns: {sorted(miss)}')
    x=df.copy(); x['timestamp']=pd.to_datetime(x['timestamp'],utc=True); x=x.sort_values('timestamp').reset_index(drop=True)
    held=x.target_exposure.astype(float).shift(1,fill_value=0.0)
    turn=held.diff().abs(); turn.iloc[0]=abs(held.iloc[0])
    cost=turn*(fee_bps_one_way+slippage_bps_one_way)/10000.0
    pnl=np.zeros(len(x));
    for i in range(1,len(x)):
        old=float(held.iloc[i-1]); new=float(held.iloc[i]); pc=float(x.close.iloc[i-1]); op=float(x.open.iloc[i]); cl=float(x.close.iloc[i])
        pnl[i]=old*(op/pc-1)+new*(cl/op-1)
    net=pnl-cost.to_numpy(); eq=np.cumprod(1+net)
    out=x.copy(); out['held_exposure']=held; out['turnover']=turn; out['trade_cost']=cost; out['net_return']=net; out['equity']=eq
    return out

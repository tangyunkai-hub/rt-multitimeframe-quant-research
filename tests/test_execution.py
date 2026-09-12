import pandas as pd
from rtquant.execution import simulate_next_open

def test_next_open_no_same_bar_fill():
    x=pd.DataFrame([
      {'timestamp':'2026-10-01T00:00:00Z','open':100,'close':100,'target_exposure':1},
      {'timestamp':'2026-10-01T02:00:00Z','open':102,'close':103,'target_exposure':1},
    ])
    y=simulate_next_open(x,fee_bps_one_way=0)
    assert y.held_exposure.iloc[0]==0
    assert y.held_exposure.iloc[1]==1

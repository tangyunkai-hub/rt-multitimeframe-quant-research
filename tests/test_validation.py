import pandas as pd
from rtquant.validation import evaluate_paired_divergence

def test_paired_delta_prefers_flat_when_short_loses():
    x=pd.DataFrame([
      {'timestamp':'2026-10-01T00:00:00Z','close':100,'A_core':'FLAT','B_core':'FLAT'},
      {'timestamp':'2026-10-01T02:00:00Z','close':100,'A_core':'CORE_SHORT','B_core':'FLAT'},
      {'timestamp':'2026-10-01T04:00:00Z','close':105,'A_core':'CORE_SHORT','B_core':'FLAT'},
      {'timestamp':'2026-10-01T06:00:00Z','close':106,'A_core':'FLAT','B_core':'FLAT'},
    ])
    r=evaluate_paired_divergence(x)
    assert r['total_paired_delta_log']>0
    assert len(r['segments'])==1

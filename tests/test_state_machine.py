from rtquant.core import *

def test_candidate_b_suppresses_only_short_reentry():
    A=CampaignEngine(); B=CandidateBEngine(); a=b=State()
    seq=[Event('t1',EventType.MAJOR_BEAR_CONFIRMED),Event('t2',EventType.LOCAL_SHORT_ENTRY),Event('t3',EventType.LOCAL_SHORT_INVALIDATION),Event('t4',EventType.LOCAL_SHORT_REENTRY)]
    for e in seq: a=A.apply(a,e); b=B.apply(b,e)
    assert a.core==Core.SHORT
    assert b.core==Core.FLAT
    assert b.last_action=='PROBE_SHORT_REENTRY_SUPPRESSED'

def test_opposite_confirmed_exits_core():
    e=CampaignEngine(); s=State(regime=Regime.BEAR,core=Core.SHORT)
    s=e.apply(s,Event('t',EventType.MAJOR_BULL_CONFIRMED))
    assert s.core==Core.FLAT and s.regime==Regime.BULL

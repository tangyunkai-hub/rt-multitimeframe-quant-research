from rtquant.paper import PaperState, process_bar

def test_idempotency():
    row={'timestamp':'2026-10-01T00:00:00Z','open':100,'close':101,'target_exposure':1}
    s,a=process_bar(PaperState(),row)
    s2,a2=process_bar(s,row)
    assert a2['status']=='IDEMPOTENT_NOOP'
    assert s2==s

import pandas as pd, pytest
from rtquant.io import validate_events

def test_freeze_rejection():
    x=pd.DataFrame([{'timestamp':'2026-09-12T02:00:00Z','event_type':'MAJOR_BEAR_CONFIRMED'}])
    with pytest.raises(ValueError): validate_events(x,freeze='2026-09-12T02:00:00Z')

def test_unknown_event_rejected():
    x=pd.DataFrame([{'timestamp':'2026-10-01T00:00:00Z','event_type':'MAGIC'}])
    with pytest.raises(ValueError): validate_events(x)

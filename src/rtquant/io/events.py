import pandas as pd
from rtquant.core.state_machine import EventType

REQUIRED = {"timestamp", "event_type"}

def validate_events(df: pd.DataFrame, *, freeze=None) -> pd.DataFrame:
    miss=REQUIRED-set(df.columns)
    if miss: raise ValueError(f"missing required columns: {sorted(miss)}")
    x=df.copy(); x['timestamp']=pd.to_datetime(x['timestamp'],utc=True)
    if x['timestamp'].isna().any(): raise ValueError('invalid timestamp')
    allowed={e.value for e in EventType}
    bad=sorted(set(x['event_type'])-allowed)
    if bad: raise ValueError(f"unknown event type(s): {bad}")
    if freeze is not None and (x['timestamp'] <= pd.Timestamp(freeze)).any():
        raise ValueError('pre-freeze event rejected')
    if x.duplicated(['timestamp','event_type']).any(): raise ValueError('duplicate event')
    return x.sort_values('timestamp', kind='stable').reset_index(drop=True)

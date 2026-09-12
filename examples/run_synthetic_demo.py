from pathlib import Path
import pandas as pd
from rtquant.core import CampaignEngine, CandidateBEngine, Event, EventType, State
from rtquant.io import validate_events
from rtquant.execution import simulate_next_open

HERE=Path(__file__).resolve().parent
events=validate_events(pd.read_csv(HERE/'synthetic_events.csv'))
a=CampaignEngine(); b=CandidateBEngine(); sa=sb=State()
print('Candidate A vs B state trace')
for r in events.itertuples(index=False):
    ev=Event(str(r.timestamp),EventType(r.event_type))
    sa=a.apply(sa,ev); sb=b.apply(sb,ev)
    print(r.timestamp, r.event_type, 'A=',sa.core.value,sa.last_action,'B=',sb.core.value,sb.last_action)
print('\nNext-open execution demo')
print(simulate_next_open(pd.read_csv(HERE/'synthetic_bars.csv'))[['timestamp','held_exposure','equity']].to_string(index=False))

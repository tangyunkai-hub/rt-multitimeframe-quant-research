import importlib.util
import json
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("forward_bitstamp", ROOT / "tools" / "download_forward_bitstamp_state.py")
mod = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)


def fake_raw(market, step, start_open, end_open):
    freeze = int(mod.FREEZE.timestamp())
    opens = [freeze-step, freeze, freeze+step]
    rows=[]
    for t in opens:
        if start_open <= t <= end_open:
            rows.append({"open_time":pd.to_datetime(t,unit="s",utc=True),"availability_time":pd.to_datetime(t+step,unit="s",utc=True),
                         "open":100.0,"high":102.0,"low":99.0,"close":101.0,"volume":1.0})
    return pd.DataFrame(rows), [{"market":market,"step":step,"rows":len(rows)}]


def test_forward_bitstamp_filters_by_availability_and_never_pnl(tmp_path):
    gate=mod.collect_forward_state(out=tmp_path,end_day=date(2026,9,13),mode="full",raw_collector=fake_raw)
    assert gate["status"] == "PASS"
    assert gate["state_only"] is True
    assert gate["price_pnl_use_allowed"] is False
    for label in ("12h","1d"):
        d=pd.read_csv(tmp_path/"bitstamp"/f"BTCUSD_{label}_forward.csv.gz")
        t=pd.to_datetime(d.availability_time,utc=True)
        assert (t > mod.FREEZE).all()
        assert (t <= pd.Timestamp("2026-09-14T00:00:00Z")).all()


def test_forward_bitstamp_waits_before_complete_postfreeze_cutoff(tmp_path):
    gate=mod.collect_forward_state(out=tmp_path,end_day=date(2026,9,11),mode="full",raw_collector=fake_raw)
    assert gate["status"] == "WAITING_NO_COMPLETED_POST_FREEZE_UTC_DAY"
    assert gate["performance_evaluation_allowed"] is False

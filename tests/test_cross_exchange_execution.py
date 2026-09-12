import importlib.util
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("cross_exchange", ROOT / "tools" / "evaluate_cross_exchange_coinbase.py")
CE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CE)


def _source(times, opens, closes):
    open_time = pd.to_datetime(times, utc=True)
    return pd.DataFrame(
        {
            "open_time": open_time,
            "availability_time": open_time + pd.Timedelta(minutes=15),
            "open": opens,
            "high": [max(o, c) for o, c in zip(opens, closes)],
            "low": [min(o, c) for o, c in zip(opens, closes)],
            "close": closes,
            "volume": 1.0,
        }
    )


def _timeline(times, sides):
    return pd.DataFrame(
        {"core_side": sides, "major_direction": -1, "major_at_risk": False},
        index=pd.to_datetime(times, utc=True),
    )


def test_decision_fills_only_at_next_observed_open():
    source = _source(
        ["2020-01-01 00:00", "2020-01-01 00:15", "2020-01-01 00:30"],
        [100, 100, 90],
        [100, 90, 90],
    )
    timeline = _timeline(["2020-01-01 00:15"], [-1])
    executed = CE.execute(source, timeline, 0)
    assert executed.held_exposure.tolist() == [0.0, -1.0, -1.0]
    assert abs(executed.net_return.iloc[1] - 0.10) < 1e-12


def test_missing_bar_does_not_create_phantom_fill():
    source = _source(
        ["2020-01-01 00:00", "2020-01-01 00:30"],
        [100, 80],
        [100, 72],
    )
    timeline = _timeline(["2020-01-01 00:15"], [-1])
    executed = CE.execute(source, timeline, 0)
    assert executed.held_exposure.tolist() == [0.0, -1.0]
    # The 100 -> 80 venue gap occurs before the next observed fill, so the new
    # short receives only the 80 -> 72 intrabar move.
    assert abs(executed.net_return.iloc[1] - 0.10) < 1e-12


def test_candidate_b_only_removes_candidate_a_short():
    a = _timeline(["2020-01-01 00:15", "2020-01-01 00:45"], [-1, 0])
    b = _timeline(["2020-01-01 00:15", "2020-01-01 00:45"], [0, 0])
    inv = CE.structural_invariants(a, b)
    assert inv.failures.sum() == 0

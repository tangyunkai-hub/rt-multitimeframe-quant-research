import pandas as pd
import pytest

from rtquant.execution import simulate_next_open


def test_next_open_no_same_bar_fill():
    x = pd.DataFrame([
        {"timestamp":"2026-10-01T00:00:00Z","open":100,"close":100,"target_exposure":1},
        {"timestamp":"2026-10-01T02:00:00Z","open":102,"close":103,"target_exposure":1},
    ])
    y = simulate_next_open(x, fee_bps_one_way=0)
    assert y.held_exposure.iloc[0] == 0
    assert y.held_exposure.iloc[1] == 1


def test_gap_is_owned_by_old_exposure_until_next_open_fill():
    x = pd.DataFrame([
        {"timestamp":"2026-10-01T00:00:00Z","open":100,"close":100,"target_exposure":1},
        {"timestamp":"2026-10-01T00:15:00Z","open":100,"close":110,"target_exposure":0},
        {"timestamp":"2026-10-01T02:00:00Z","open":121,"close":121,"target_exposure":0},
    ])
    y = simulate_next_open(x, fee_bps_one_way=0)
    assert y.held_exposure.tolist() == [0.0, 1.0, 0.0]
    assert y.gap_return_component.iloc[2] == pytest.approx(0.10)
    assert y.intrabar_return_component.iloc[2] == pytest.approx(0.0)
    assert y.equity.iloc[-1] == pytest.approx(1.21)


def test_gap_and_intrabar_returns_compound_not_add():
    x = pd.DataFrame([
        {"timestamp":"2026-10-01T00:00:00Z","open":100,"close":100,"target_exposure":1},
        {"timestamp":"2026-10-01T00:15:00Z","open":100,"close":110,"target_exposure":1},
        {"timestamp":"2026-10-01T02:00:00Z","open":121,"close":133.1,"target_exposure":1},
    ])
    y = simulate_next_open(x, fee_bps_one_way=0)
    assert y.gap_return_component.iloc[2] == pytest.approx(0.10)
    assert y.intrabar_return_component.iloc[2] == pytest.approx(0.10)
    assert y.net_return.iloc[2] == pytest.approx(0.21)
    assert y.equity.iloc[-1] == pytest.approx(1.331)


def test_transaction_cost_is_applied_at_next_open_turnover():
    x = pd.DataFrame([
        {"timestamp":"2026-10-01T00:00:00Z","open":100,"close":100,"target_exposure":1},
        {"timestamp":"2026-10-01T00:15:00Z","open":100,"close":100,"target_exposure":1},
    ])
    y = simulate_next_open(x, fee_bps_one_way=10, slippage_bps_one_way=0)
    assert y.turnover.iloc[1] == pytest.approx(1.0)
    assert y.trade_cost.iloc[1] == pytest.approx(0.001)
    assert y.equity.iloc[1] == pytest.approx(0.999)


def test_duplicate_timestamps_fail_closed():
    x = pd.DataFrame([
        {"timestamp":"2026-10-01T00:00:00Z","open":100,"close":100,"target_exposure":0},
        {"timestamp":"2026-10-01T00:00:00+00:00","open":100,"close":100,"target_exposure":0},
    ])
    with pytest.raises(ValueError, match="duplicate timestamp"):
        simulate_next_open(x)


def test_invalid_prices_and_costs_fail_closed():
    x = pd.DataFrame([
        {"timestamp":"2026-10-01T00:00:00Z","open":0,"close":100,"target_exposure":0},
    ])
    with pytest.raises(ValueError, match="prices must be positive"):
        simulate_next_open(x)
    with pytest.raises(ValueError, match="cost assumptions"):
        simulate_next_open(x.assign(open=100), fee_bps_one_way=-1)

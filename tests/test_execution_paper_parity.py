import pandas as pd
import pytest

from rtquant.execution import simulate_next_open
from rtquant.paper import PaperState, process_bar


def test_execution_simulator_matches_incremental_paper_runner_bar_by_bar():
    rows = [
        {"timestamp":"2026-10-01T00:00:00Z","open":100.0,"close":101.0,"target_exposure":1.0},
        {"timestamp":"2026-10-01T00:15:00Z","open":102.0,"close":104.0,"target_exposure":1.0},
        {"timestamp":"2026-10-01T01:00:00Z","open":99.0,"close":98.0,"target_exposure":0.4},
        {"timestamp":"2026-10-01T01:15:00Z","open":97.0,"close":100.0,"target_exposure":0.0},
        {"timestamp":"2026-10-01T03:00:00Z","open":101.0,"close":99.0,"target_exposure":-0.5},
    ]
    fee = 7.0
    slippage = 2.0
    batch = simulate_next_open(
        pd.DataFrame(rows),
        fee_bps_one_way=fee,
        slippage_bps_one_way=slippage,
    )

    state = PaperState()
    paper_equity = []
    paper_held = []
    for row in rows:
        state, action = process_bar(
            state,
            row,
            fee_bps_one_way=fee,
            slippage_bps_one_way=slippage,
        )
        assert action["status"] == "PROCESSED"
        paper_equity.append(state.equity)
        paper_held.append(state.held_exposure)

    assert paper_equity == pytest.approx(batch["equity"].tolist())
    assert paper_held == pytest.approx(batch["held_exposure"].tolist())


def test_parity_includes_gap_old_exposure_semantics():
    rows = [
        {"timestamp":"2026-10-01T00:00:00Z","open":100,"close":100,"target_exposure":1},
        {"timestamp":"2026-10-01T00:15:00Z","open":100,"close":110,"target_exposure":0},
        {"timestamp":"2026-10-01T04:00:00Z","open":121,"close":121,"target_exposure":0},
    ]
    batch = simulate_next_open(pd.DataFrame(rows), fee_bps_one_way=0)

    state = PaperState()
    for row in rows:
        state, _ = process_bar(state, row, fee_bps_one_way=0)

    assert state.equity == pytest.approx(1.21)
    assert state.equity == pytest.approx(batch["equity"].iloc[-1])

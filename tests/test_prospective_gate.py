import pandas as pd
import pytest

from rtquant.validation import (
    assess_candidate_b_information_floor,
    prospective_release_gate,
)

FREEZE = pd.Timestamp("2026-09-12T02:00:00Z")


def _frame(*, end_days=200, include_close=True):
    # Six separated A/B divergence segments spread across three Bear epochs.
    day_offsets = [1, 2, 40, 41, 80, 81, 120, 121, 160, 161, end_days - 1, end_days]
    rows = []
    divergent_slots = {0: 1, 2: 1, 4: 2, 6: 2, 8: 3, 10: 3}
    for i, day in enumerate(day_offsets):
        divergent = i in divergent_slots
        row = {
            "timestamp": (FREEZE + pd.Timedelta(days=day)).isoformat(),
            "A_core": "CORE_SHORT",
            "B_core": "FLAT" if divergent else "CORE_SHORT",
            "major_bear_epoch_id": divergent_slots.get(i),
        }
        if include_close:
            row["close"] = 100.0 + i
        rows.append(row)
    return pd.DataFrame(rows)


def test_pre_floor_report_contains_no_performance_even_without_prices():
    x = _frame(end_days=100, include_close=False)
    out = prospective_release_gate(x)
    status = out["information_floor"]
    assert status["status"] == "INSUFFICIENT_FORWARD_EVIDENCE"
    assert status["performance_release_allowed"] is False
    assert out["performance"] is None
    assert out["next_action"] == "KEEP_PERFORMANCE_EMBARGOED"


def test_floor_requires_duration_segments_and_independent_epochs():
    x = _frame(end_days=200)
    status = assess_candidate_b_information_floor(x)
    assert status.forward_days >= 180
    assert status.divergence_segments == 6
    assert status.independent_major_bear_epochs == 3
    assert status.duration_met is True
    assert status.segments_met is True
    assert status.epochs_met is True
    assert status.performance_release_allowed is True


def test_eligible_floor_authorizes_only_frozen_private_evaluator():
    x = _frame(end_days=200, include_close=False)
    out = prospective_release_gate(x)
    assert out["information_floor"]["status"] == "ELIGIBLE_FOR_FROZEN_EVALUATOR"
    assert out["information_floor"]["performance_release_allowed"] is True
    assert out["performance"] is None
    assert out["next_action"] == "RUN_SEPARATELY_FROZEN_PRIVATE_V024_EVALUATOR"


def test_at_or_before_freeze_data_is_rejected_not_silently_filtered():
    x = _frame(end_days=200)
    x.loc[0, "timestamp"] = FREEZE.isoformat()
    with pytest.raises(ValueError, match="at/before freeze boundary"):
        assess_candidate_b_information_floor(x)


def test_duplicate_timestamps_fail_closed():
    x = _frame(end_days=200)
    x.loc[1, "timestamp"] = x.loc[0, "timestamp"]
    with pytest.raises(ValueError, match="duplicate timestamp"):
        assess_candidate_b_information_floor(x)


def test_information_floor_does_not_use_return_sign_or_magnitude():
    a = _frame(end_days=200)
    b = a.copy()
    b["close"] = list(reversed(a["close"].tolist()))
    sa = assess_candidate_b_information_floor(a)
    sb = assess_candidate_b_information_floor(b)
    assert sa == sb

import math
import pytest

from rtquant.risk import RiskBudgetPolicy, allocate_exposure


def test_multiple_hedge_reasons_use_max_not_sum():
    p = RiskBudgetPolicy(
        reduce_fraction=0.20,
        hedge_fractions={"local": 0.10, "higher": 0.25},
        gross_cap=1.0,
    )
    plan = allocate_exposure(
        p, core_side="LONG", reduced=True, hedge_reasons=["local", "higher"]
    )
    assert plan.authorized_hedge_fraction == 0.25
    assert plan.core_long == 0.75 * plan.gross_scale or plan.core_long == pytest.approx(0.8 * plan.gross_scale)
    assert plan.net_exposure >= 0


def test_reduce_is_applied_once():
    p = RiskBudgetPolicy(reduce_fraction=0.25)
    plan = allocate_exposure(p, core_side="LONG", reduced=True)
    assert plan.core_long == pytest.approx(0.75)
    assert plan.applied_reduce_fraction == pytest.approx(0.25)


def test_gross_cap_scales_authorized_legs_proportionally():
    p = RiskBudgetPolicy(
        reduce_fraction=0.0,
        hedge_fractions={"risk": 0.30},
        gross_cap=1.0,
    )
    plan = allocate_exposure(p, core_side="LONG", hedge_reasons=["risk"])
    assert plan.gross_exposure == pytest.approx(1.0)
    assert plan.gross_scale == pytest.approx(1.0 / 1.30)
    assert plan.core_long / plan.hedge_short == pytest.approx(1.0 / 0.30)


def test_long_defense_never_flips_net_short():
    p = RiskBudgetPolicy(
        reduce_fraction=0.80,
        hedge_fractions={"risk": 0.90},
        gross_cap=1.0,
    )
    plan = allocate_exposure(
        p, core_side="LONG", reduced=True, hedge_reasons=["risk"]
    )
    assert plan.hedge_short == pytest.approx(plan.core_long)
    assert plan.net_exposure == pytest.approx(0.0)


def test_flat_cannot_gain_exposure_from_risk_layer():
    p = RiskBudgetPolicy(
        reduce_fraction=0.50,
        hedge_fractions={"risk": 0.30},
        gross_cap=1.0,
    )
    plan = allocate_exposure(
        p, core_side="FLAT", reduced=True, hedge_reasons=["risk"]
    )
    assert plan.gross_exposure == 0.0
    assert plan.net_exposure == 0.0


def test_short_is_unchanged_because_protective_long_mirror_is_disabled():
    p = RiskBudgetPolicy(
        reduce_fraction=0.50,
        hedge_fractions={"risk": 0.30},
        gross_cap=1.0,
    )
    plan = allocate_exposure(
        p, core_side="SHORT", reduced=True, hedge_reasons=["risk"]
    )
    assert plan.core_short == pytest.approx(1.0)
    assert plan.hedge_short == 0.0
    assert plan.net_exposure == pytest.approx(-1.0)


def test_unknown_hedge_reason_fails_closed_for_long():
    p = RiskBudgetPolicy(hedge_fractions={"known": 0.10})
    with pytest.raises(ValueError, match="unknown hedge reason"):
        allocate_exposure(p, core_side="LONG", hedge_reasons=["unknown"])


def test_invalid_policy_fractions_rejected():
    with pytest.raises(ValueError):
        RiskBudgetPolicy(reduce_fraction=1.1)
    with pytest.raises(ValueError):
        RiskBudgetPolicy(hedge_fractions={"risk": -0.1})

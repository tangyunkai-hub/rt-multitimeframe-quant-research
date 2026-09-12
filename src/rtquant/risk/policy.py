from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Iterable


@dataclass(frozen=True)
class RiskBudgetPolicy:
    """Public-safe capital overlay policy.

    Exact private benchmark fractions are intentionally not embedded here.  The
    policy layer only encodes the frozen architecture: one reduction fraction,
    non-additive hedge reasons, and an optional gross-exposure cap.
    """

    core_unit: float = 1.0
    reduce_fraction: float = 0.0
    hedge_fractions: Mapping[str, float] | None = None
    gross_cap: float | None = None

    def __post_init__(self):
        if not 0 < float(self.core_unit) <= 1.0:
            raise ValueError("core_unit must be in (0, 1]")
        if not 0 <= float(self.reduce_fraction) <= 1.0:
            raise ValueError("reduce_fraction must be in [0, 1]")
        if self.gross_cap is not None and float(self.gross_cap) <= 0:
            raise ValueError("gross_cap must be positive")
        for reason, fraction in (self.hedge_fractions or {}).items():
            if not reason:
                raise ValueError("hedge reason names must be non-empty")
            if not 0 <= float(fraction) <= 1.0:
                raise ValueError("hedge fractions must be in [0, 1]")


@dataclass(frozen=True)
class ExposurePlan:
    core_long: float
    core_short: float
    hedge_short: float
    gross_exposure: float
    net_exposure: float
    gross_scale: float
    applied_reduce_fraction: float
    authorized_hedge_fraction: float


def _max_authorized_hedge(policy: RiskBudgetPolicy, reasons: Iterable[str]) -> float:
    mapping = dict(policy.hedge_fractions or {})
    values = []
    for reason in set(reasons):
        if reason not in mapping:
            raise ValueError(f"unknown hedge reason: {reason}")
        values.append(float(mapping[reason]))
    return max(values, default=0.0)


def allocate_exposure(
    policy: RiskBudgetPolicy,
    *,
    core_side: str,
    reduced: bool = False,
    hedge_reasons: Iterable[str] = (),
) -> ExposurePlan:
    """Translate frozen risk states into capital legs without changing permission.

    The v0.26 public architecture is a Long-defense sandbox.  Risk inputs cannot
    create exposure from FLAT and cannot alter CORE_SHORT because the protective-
    long mirror remains disabled.  For CORE_LONG, reduction is applied once;
    multiple hedge reasons authorize the maximum fraction rather than summing.
    A gross cap, when supplied, proportionally scales already-authorized legs.
    """

    side = str(core_side).upper()
    unit = float(policy.core_unit)

    if side == "FLAT":
        return ExposurePlan(0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0)

    if side == "SHORT":
        # v0.26 Phase A is Long-defense only.  Do not invent a protective-long mirror.
        return ExposurePlan(0.0, unit, 0.0, unit, -unit, 1.0, 0.0, 0.0)

    if side != "LONG":
        raise ValueError("core_side must be LONG, SHORT, or FLAT")

    reduce_fraction = float(policy.reduce_fraction) if reduced else 0.0
    core_long = unit * (1.0 - reduce_fraction)
    requested_hedge = _max_authorized_hedge(policy, hedge_reasons)

    # Long defense is never allowed to reverse the portfolio net short.
    hedge_short = min(requested_hedge, core_long)
    gross = core_long + hedge_short
    scale = 1.0
    if policy.gross_cap is not None and gross > float(policy.gross_cap):
        scale = float(policy.gross_cap) / gross
        core_long *= scale
        hedge_short *= scale
        gross = float(policy.gross_cap)

    net = core_long - hedge_short
    if net < -1e-12:
        raise AssertionError("CORE_LONG defense flipped net exposure below zero")

    return ExposurePlan(
        core_long=core_long,
        core_short=0.0,
        hedge_short=hedge_short,
        gross_exposure=gross,
        net_exposure=max(net, 0.0),
        gross_scale=scale,
        applied_reduce_fraction=reduce_fraction,
        authorized_hedge_fraction=requested_hedge,
    )

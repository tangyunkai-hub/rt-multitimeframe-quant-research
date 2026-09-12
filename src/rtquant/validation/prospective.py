from __future__ import annotations

from dataclasses import dataclass, asdict
import pandas as pd

from .paired import evaluate_paired_divergence


CANDIDATE_B_FREEZE_UTC = pd.Timestamp("2026-09-12T02:00:00Z")


@dataclass(frozen=True)
class ProspectiveFloorStatus:
    freeze_boundary_utc: str
    last_observation_utc: str | None
    forward_days: float
    divergence_segments: int
    independent_major_bear_epochs: int
    min_forward_days: int
    min_divergence_segments: int
    min_major_bear_epochs: int
    duration_met: bool
    segments_met: bool
    epochs_met: bool
    performance_release_allowed: bool
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def _validated_forward_frame(df: pd.DataFrame, freeze_boundary) -> pd.DataFrame:
    req = {"timestamp", "A_core", "B_core", "major_bear_epoch_id"}
    missing = req - set(df.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")

    x = df.copy()
    x["timestamp"] = pd.to_datetime(x["timestamp"], utc=True, errors="coerce")
    if x["timestamp"].isna().any():
        raise ValueError("invalid timestamp")
    x = x.sort_values("timestamp", kind="mergesort").reset_index(drop=True)
    if x["timestamp"].duplicated().any():
        raise ValueError("duplicate timestamp")

    freeze = pd.Timestamp(freeze_boundary)
    freeze = freeze.tz_localize("UTC") if freeze.tzinfo is None else freeze.tz_convert("UTC")
    if len(x) and (x["timestamp"] <= freeze).any():
        raise ValueError("prospective pool contains observation at/before freeze boundary")

    allowed = {"CORE_LONG", "CORE_SHORT", "FLAT"}
    for col in ("A_core", "B_core"):
        bad = set(x[col].dropna().astype(str)) - allowed
        if bad:
            raise ValueError(f"invalid {col} states: {sorted(bad)}")
        if x[col].isna().any():
            raise ValueError(f"missing {col} state")
    return x


def assess_candidate_b_information_floor(
    df: pd.DataFrame,
    *,
    freeze_boundary=CANDIDATE_B_FREEZE_UTC,
    min_forward_days: int = 180,
    min_divergence_segments: int = 6,
    min_major_bear_epochs: int = 3,
) -> ProspectiveFloorStatus:
    """Count information only; never compute or expose Candidate A/B performance."""
    x = _validated_forward_frame(df, freeze_boundary)
    freeze = pd.Timestamp(freeze_boundary)
    freeze = freeze.tz_localize("UTC") if freeze.tzinfo is None else freeze.tz_convert("UTC")

    if len(x):
        last_ts = x["timestamp"].iloc[-1]
        forward_days = max(0.0, (last_ts - freeze).total_seconds() / 86400.0)
    else:
        last_ts = None
        forward_days = 0.0

    divergent = x["A_core"].ne(x["B_core"]) if len(x) else pd.Series(dtype=bool)
    if len(x):
        starts = divergent & ~divergent.shift(1, fill_value=False)
        segments = int(starts.sum())
        epochs = int(x.loc[divergent, "major_bear_epoch_id"].dropna().nunique())
    else:
        segments = 0
        epochs = 0

    duration_met = forward_days >= min_forward_days
    segments_met = segments >= min_divergence_segments
    epochs_met = epochs >= min_major_bear_epochs
    eligible = bool(duration_met and segments_met and epochs_met)

    return ProspectiveFloorStatus(
        freeze_boundary_utc=freeze.isoformat(),
        last_observation_utc=last_ts.isoformat() if last_ts is not None else None,
        forward_days=float(forward_days),
        divergence_segments=segments,
        independent_major_bear_epochs=epochs,
        min_forward_days=int(min_forward_days),
        min_divergence_segments=int(min_divergence_segments),
        min_major_bear_epochs=int(min_major_bear_epochs),
        duration_met=duration_met,
        segments_met=segments_met,
        epochs_met=epochs_met,
        performance_release_allowed=eligible,
        status="ELIGIBLE_FOR_FROZEN_JUDGEMENT" if eligible else "INSUFFICIENT_FORWARD_EVIDENCE",
    )


def evaluate_candidate_b_prospectively(
    df: pd.DataFrame,
    *,
    freeze_boundary=CANDIDATE_B_FREEZE_UTC,
    round_trip_bps: float = 14.0,
    min_forward_days: int = 180,
    min_divergence_segments: int = 6,
    min_major_bear_epochs: int = 3,
) -> dict:
    """Release paired performance only after the preregistered information floor.

    Before eligibility, the return object contains counts/status only and does not
    call the paired performance evaluator.  This is an anti-optional-stopping guard,
    not evidence that the eventual result will be favorable.
    """
    status = assess_candidate_b_information_floor(
        df,
        freeze_boundary=freeze_boundary,
        min_forward_days=min_forward_days,
        min_divergence_segments=min_divergence_segments,
        min_major_bear_epochs=min_major_bear_epochs,
    )
    out = {"information_floor": status.to_dict(), "performance": None}
    if not status.performance_release_allowed:
        return out

    req = {"close"}
    missing = req - set(df.columns)
    if missing:
        raise ValueError(f"missing columns required after evidence floor: {sorted(missing)}")
    x = _validated_forward_frame(df, freeze_boundary)
    performance = evaluate_paired_divergence(x, round_trip_bps=round_trip_bps)
    out["performance"] = performance
    return out

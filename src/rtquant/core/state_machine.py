from __future__ import annotations
from dataclasses import dataclass, replace
from enum import Enum

class Regime(str, Enum):
    BULL = "BULL_CONFIRMED"
    BULL_AT_RISK = "BULL_AT_RISK"
    BEAR = "BEAR_CONFIRMED"
    BEAR_AT_RISK = "BEAR_AT_RISK"
    NEUTRAL = "NEUTRAL"

class Core(str, Enum):
    FLAT = "FLAT"
    LONG = "CORE_LONG"
    SHORT = "CORE_SHORT"

class EventType(str, Enum):
    MAJOR_BULL_CONFIRMED = "MAJOR_BULL_CONFIRMED"
    MAJOR_BEAR_CONFIRMED = "MAJOR_BEAR_CONFIRMED"
    MAJOR_BULL_RISK = "MAJOR_BULL_RISK"
    MAJOR_BEAR_RISK = "MAJOR_BEAR_RISK"
    LOCAL_LONG_ENTRY = "LOCAL_LONG_ENTRY"
    LOCAL_SHORT_ENTRY = "LOCAL_SHORT_ENTRY"
    LOCAL_LONG_RISK = "LOCAL_LONG_RISK"
    LOCAL_SHORT_INVALIDATION = "LOCAL_SHORT_INVALIDATION"
    LOCAL_LONG_RECOVERY = "LOCAL_LONG_RECOVERY"
    LOCAL_SHORT_RECOVERY = "LOCAL_SHORT_RECOVERY"
    LOCAL_LONG_REENTRY = "LOCAL_LONG_REENTRY"
    LOCAL_SHORT_REENTRY = "LOCAL_SHORT_REENTRY"

@dataclass(frozen=True)
class Event:
    timestamp: str
    type: EventType
    note: str = ""

@dataclass(frozen=True)
class State:
    regime: Regime = Regime.NEUTRAL
    core: Core = Core.FLAT
    at_risk: bool = False
    reentry_watch: str | None = None
    last_action: str = "HOLD"

class CampaignEngine:
    """Generic public demonstration of the private campaign-authority layer."""
    def apply(self, s: State, e: Event) -> State:
        if e.type == EventType.MAJOR_BULL_CONFIRMED:
            return replace(s, regime=Regime.BULL, core=Core.FLAT if s.core==Core.SHORT else s.core,
                           at_risk=False, reentry_watch=None, last_action="MAJOR_BULL_CONFIRMED")
        if e.type == EventType.MAJOR_BEAR_CONFIRMED:
            return replace(s, regime=Regime.BEAR, core=Core.FLAT if s.core==Core.LONG else s.core,
                           at_risk=False, reentry_watch=None, last_action="MAJOR_BEAR_CONFIRMED")
        if e.type == EventType.MAJOR_BULL_RISK and s.regime in (Regime.BULL, Regime.BULL_AT_RISK):
            return replace(s, regime=Regime.BULL_AT_RISK, at_risk=True, last_action="RISK_DOWNGRADE")
        if e.type == EventType.MAJOR_BEAR_RISK and s.regime in (Regime.BEAR, Regime.BEAR_AT_RISK):
            return replace(s, regime=Regime.BEAR_AT_RISK, at_risk=True, last_action="RISK_DOWNGRADE")
        if e.type == EventType.LOCAL_LONG_ENTRY and s.core==Core.FLAT and s.regime in (Regime.BULL,Regime.BULL_AT_RISK):
            return replace(s, core=Core.LONG, last_action="ENTER_LONG")
        if e.type == EventType.LOCAL_SHORT_ENTRY and s.core==Core.FLAT and s.regime in (Regime.BEAR,Regime.BEAR_AT_RISK):
            return replace(s, core=Core.SHORT, last_action="ENTER_SHORT")
        if e.type == EventType.LOCAL_SHORT_INVALIDATION and s.core==Core.SHORT:
            return replace(s, core=Core.FLAT, reentry_watch="SHORT", last_action="EXIT_SHORT")
        if e.type == EventType.LOCAL_LONG_RISK and s.core==Core.LONG:
            return replace(s, at_risk=True, last_action="LONG_RISK")
        if e.type == EventType.LOCAL_LONG_RECOVERY and s.regime in (Regime.BULL,Regime.BULL_AT_RISK):
            return replace(s, regime=Regime.BULL, at_risk=False, last_action="LONG_RECOVERY")
        if e.type == EventType.LOCAL_SHORT_RECOVERY and s.regime in (Regime.BEAR,Regime.BEAR_AT_RISK):
            return replace(s, regime=Regime.BEAR, at_risk=False, last_action="SHORT_RECOVERY")
        if e.type == EventType.LOCAL_LONG_REENTRY and s.core==Core.FLAT and s.reentry_watch=="LONG" and s.regime in (Regime.BULL,Regime.BULL_AT_RISK):
            return replace(s, core=Core.LONG, reentry_watch=None, last_action="REENTER_LONG")
        if e.type == EventType.LOCAL_SHORT_REENTRY and s.core==Core.FLAT and s.reentry_watch=="SHORT" and s.regime in (Regime.BEAR,Regime.BEAR_AT_RISK):
            return replace(s, core=Core.SHORT, reentry_watch=None, last_action="REENTER_SHORT")
        return replace(s, last_action="HOLD")

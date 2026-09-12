from dataclasses import replace
from .state_machine import CampaignEngine, State, Event, EventType, Core, Regime

class CandidateBEngine(CampaignEngine):
    """Public abstraction of the post-holdout one-permission hypothesis.

    When an active same-regime Short re-entry watch exists, the re-entry event is
    retained as a probe/diagnostic observation but does not automatically restore core Short.
    """
    def apply(self, s: State, e: Event) -> State:
        if (e.type == EventType.LOCAL_SHORT_REENTRY and s.core == Core.FLAT and
            s.reentry_watch == "SHORT" and s.regime in (Regime.BEAR,Regime.BEAR_AT_RISK)):
            return replace(s, last_action="PROBE_SHORT_REENTRY_SUPPRESSED")
        return super().apply(s, e)

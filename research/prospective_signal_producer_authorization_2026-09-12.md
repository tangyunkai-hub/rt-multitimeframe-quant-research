# v0.24 Prospective Signal-Producer Authorization Status

**Date:** 2026-09-12  
**Current status:** `BLOCKED_PROSPECTIVE_SIGNAL_PRODUCER_NOT_FROZEN`

## Decision boundary

The public forward-native collector and the v0.24 prospective artifact/provenance contract are operational, but there is currently no separately frozen native-data -> normalized-event/state producer authorized for v0.24 prospective confirmation.

The implementation-compatibility-v3 adapter is **not** silently promoted into that role. Its frozen classification is `EXTERNAL_HISTORICAL_VALIDATION_NOT_PROSPECTIVE`, and its stated eligibility consequence was limited to the 2017-2022 external historical program. Semantic regression success does not, by itself, change an experiment's authorized use.

Likewise, the original v0.24 shadow runner consumes a normalized event ledger; it does not define a raw Binance OHLC -> proprietary signal/event reconstruction. Inventing that missing transformation now inside the public repository would create an unregistered data/semantic change.

## Operational consequence

`rtquant-prospective-intake` may:

1. rebuild the complete post-freeze native source pool with the public `full` collector;
2. verify that the source DATA_GATE is complete and performance/judgement remain embargoed;
3. stop with `BLOCKED_PROSPECTIVE_SIGNAL_PRODUCER_NOT_FROZEN` until a prospective producer is separately frozen;
4. after a future freeze, verify that producer's exact SHA-256 before accepting its state ledger;
5. bind the resulting state ledger to source bytes and frozen protocol commitments through the prospective artifact contract.

There is intentionally no CLI flag that can override the producer commitment.

## What would unblock this gate

Before any Candidate B forward performance is read, freeze a prospective signal-producer protocol that specifies the exact source/timeframe mapping, closed-bar availability semantics, proprietary indicator/event implementation identity, initial-state continuity, and regression requirements. The producer must receive a version and SHA-256 commitment and must pass semantic/invariant regression before it is added to the public authorization constant.

If that producer changes strategy semantics rather than only reproducing the already-frozen implementation, it is a new candidate/version and requires a new freeze boundary. No consumed forward observations may be reused to validate a change motivated by their performance.

## Research status unchanged

- v0.22 remains `HOLDOUT_FAIL_NOT_DEPLOYMENT_READY`.
- Candidate B remains `FROZEN_HYPOTHESIS_NOT_VALIDATED`.
- v0.24 remains `INSUFFICIENT_FORWARD_EVIDENCE`.
- No Candidate B prospective performance has been released.
- Deployment remains unauthorized.

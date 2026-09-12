# v0.24 Prospective Signal-Producer Authorization Status

**Updated:** 2026-09-13  
**Current status:** `BLOCKED_PROSPECTIVE_INPUT_CONTINUITY_NOT_FROZEN`

## Frozen implementation now exists

A private prospective producer implementation has been frozen without reading or computing Candidate B forward performance. Its public byte commitment is:

- producer: `v024_prospective_signal_producer_v1`
- SHA-256: `c2f2a47cf4a22d975a75c922eec3d0cb6d65664180fdf80246b302ac80ed8ceb`
- consumed semantic-regression window: 2023-06-01 through 2026-01-10
- campaign timestamps compared: 45,807
- authority-critical state/action mismatches: 0
- Candidate B integration isolation: PASS

The first regression-harness attempt failed because its comparison-window initialization truncated prior W7 watch state. That failed attempt is preserved privately. The reference methodology was corrected by constructing full consumed-history state before slicing the comparison window; no strategy semantic was changed.

This producer is a reproduction of already-frozen private semantics, not a new strategy candidate. The external-history compatibility-v3 adapter remains `EXTERNAL_HISTORICAL_VALIDATION_NOT_PROSPECTIVE` and is not relabeled as prospective evidence.

## Why operation is still blocked

Two source-continuity requirements remain separate from the producer implementation freeze:

1. an immutable consumed **pre-freeze warm-up seed** through `2026-09-12T02:00:00Z`, used only to initialize long-memory indicators/state and never counted as prospective evidence;
2. a verified post-freeze **Bitstamp BTCUSD 12h/1d state-only source chain**, with Bitstamp prices explicitly prohibited from Binance execution/PnL.

The public intake therefore commits the producer SHA now but still fails closed until the warm-up seed receives exact byte/hash commitments and the forward Bitstamp state-only gate is present.

## Operational consequence

`rtquant-prospective-intake` may collect the complete post-freeze Binance pool and the Bitstamp state-only pool, verify their data-only gates, and then stop at the warm-up-seed commitment gate. There is no CLI option that can override the producer or warm-up commitments.

Once the exact warm-up seed contract is frozen, the intake chain may verify the private producer bytes, the warm-up bytes, Binance source manifest/gate and Bitstamp state-source manifest/gate, then emit a provenance-bound state ledger. The public information gate still exposes no Candidate A/B performance before the frozen v0.24 information floor is met.

## Research status unchanged

- v0.22 remains `HOLDOUT_FAIL_NOT_DEPLOYMENT_READY`.
- Candidate B remains `FROZEN_HYPOTHESIS_NOT_VALIDATED`.
- v0.24 remains `INSUFFICIENT_FORWARD_EVIDENCE`.
- validated Alpha remains **NO**.
- small-capital live eligibility remains **NO**.

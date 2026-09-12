# v0.24 Prospective Signal-Producer Authorization Status

**Updated:** 2026-09-13  
**Current engineering status:** `INPUT_CONTINUITY_FROZEN_SOURCE_INTAKE_WAITING`

## Frozen prospective producer

A private prospective producer implementation was frozen without reading or computing Candidate B forward performance.

- producer: `v024_prospective_signal_producer_v1`
- SHA-256: `c2f2a47cf4a22d975a75c922eec3d0cb6d65664180fdf80246b302ac80ed8ceb`
- consumed semantic-regression window: 2023-06-01 through 2026-01-10
- campaign timestamps compared: 45,807
- authority-critical state/action mismatches: 0
- Candidate B integration isolation: PASS

The first regression-harness attempt failed because its comparison-window initialization truncated prior W7 watch state. That failed attempt remains preserved privately. The regression harness was corrected by constructing full consumed-history state before slicing the comparison window; no strategy semantic was changed.

The external-history compatibility-v3 adapter remains `EXTERNAL_HISTORICAL_VALIDATION_NOT_PROSPECTIVE`; it is not relabeled as prospective evidence.

## Frozen consumed warm-up seed

Long-memory state is initialized from an immutable seed containing only data available at or before the Candidate B freeze boundary. The seed is initialization-only and contributes zero prospective evidence rows.

- classification: `V024_CONSUMED_PRE_FREEZE_WARMUP_SEED`
- freeze boundary: `2026-09-12T02:00:00Z` inclusive for warm-up eligibility
- warm-up contract SHA-256: `a252b31f29bc7604225d482b9ec394c58360145f2ab57368e80860958da33085`
- seed-root SHA-256: `4d5233007551a282164a40cdb34580535454fa07d757666180dc7d83d039589f`
- prospective evidence rows: 0
- workflow run: `34723033060`
- workflow artifact: `10306991596`

The seed contains consumed Binance BTCUSDT 15m and Bitstamp BTCUSD 12h/1d source material needed only for indicator/state initialization. Its contract requires performance evaluation and Candidate B judgement to remain disabled.

## Forward source chain

The public `forward-native-data` workflow now collects both causally distinct sources under the same cutoff:

1. Binance native forward data for the frozen signal/execution architecture;
2. Bitstamp BTCUSD 12h/1d **state-only** data.

Bitstamp is hard-gated with `state_only=true` and `price_pnl_use_allowed=false`; Bitstamp prices cannot enter Binance execution/PnL.

The latest verified source-health run after the collector fix was `34724787426` and passed its enforcement step. At that run time, both Binance and Bitstamp correctly reported `WAITING_NO_COMPLETED_POST_FREEZE_UTC_DAY`; that is an expected availability state, not evidence failure and not a prospective result.

## Operational consequence

The producer commitment, warm-up commitment and forward Bitstamp state-source path are now engineered and hash-bound. `rtquant-prospective-intake` may proceed to the frozen private producer only after a formal `mode=full` source rebuild returns eligible source gates. While the source gates are WAITING, no state ledger is released and no Candidate B performance is read.

There is no CLI override for producer or warm-up commitments. Any byte mismatch, wrong source scope, Bitstamp PnL permission, or non-frozen producer fails closed.

## Research status unchanged

- v0.22 remains `HOLDOUT_FAIL_NOT_DEPLOYMENT_READY`.
- Candidate B remains `FROZEN_HYPOTHESIS_NOT_VALIDATED`.
- v0.24 remains `INSUFFICIENT_FORWARD_EVIDENCE`.
- validated Alpha remains **NO**.
- small-capital live eligibility remains **NO**.

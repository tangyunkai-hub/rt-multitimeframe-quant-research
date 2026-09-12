# External Historical Validation — Frozen A/B Evaluation Protocol

**Frozen:** 2026-09-12, after implementation-compatibility v3 passed modern semantic regression and **before** reading 2017–2022 Candidate A/B performance.

**Classification:** `EXTERNAL_HISTORICAL_VALIDATION_NOT_PROSPECTIVE`

## Primary order

1. BTCUSDT 2017–2022, subject to listing/causal warm-up availability.
2. ETHUSDT, exact same frozen mechanism as cross-asset replication.
3. No BTC or ETH result may change Candidate B, the adapter, thresholds, costs, sizing or the ETH rule.

## Execution convention

- Signal/state decisions are produced by implementation-compatibility v3.
- Binance Spot 15m is the execution and PnL clock.
- A decision known at a completed bar is filled no earlier than the next observed 15m open.
- Across exchange gaps, the old exposure carries through the gap; the new exposure begins at the next observed open.
- Primary cost is 14bp round trip, implemented as 7bp per unit of one-way turnover.
- Baseline slippage for the primary A/B comparison is 0bp; any 2bp/5bp one-way execution stress is secondary and cannot change the frozen rule.
- Bitstamp prices are state inputs only and never enter Binance PnL.

## Candidate A/B comparison unit

The primary A/B mechanism comparison uses **core exposure only**, matching the frozen v0.24 Candidate B permission question. Reduce/hedge overlays are reported separately when useful but do not redefine the A/B mechanism test.

The only admissible A/B core divergence is:

- Candidate A = `CORE_SHORT`
- Candidate B = `FLAT`

inside the same continuous Major Bear epoch after the frozen W2 structural hard-exit condition. Any other A/B authority divergence invalidates the run.

## Paired divergence segments

- A divergence segment begins on the first executed 15m bar where A and B held core exposure differs.
- It ends on the first executed bar where exposure converges again; that convergence bar is included so exit/entry turnover cost is captured.
- Segment statistic: `paired_delta_log = B_log_net - A_log_net`.
- `B_better = paired_delta_log > 0`.

## Independent replication unit

A continuous Major Bear epoch is the independent mechanism unit. Multiple divergence segments inside one Bear epoch are not counted as independent replications.

For every Bear epoch with divergence, report:

- number of divergence segments;
- summed paired delta log;
- whether Candidate B is better.

## External mechanism evidence floor

A directional external mechanism judgement requires at least:

- 180 calendar days of eligible external market history;
- 6 paired divergence segments;
- 3 independent Major Bear divergence epochs.

If the floor is not met, the result is `INSUFFICIENT_EXTERNAL_MECHANISM_EVIDENCE` regardless of sign.

If the floor is met:

- `EXTERNAL_MECHANISM_SUPPORT` when total paired delta log > 0 and at least two-thirds of Bear divergence epochs favor B;
- `ADVERSE_EXTERNAL_MECHANISM_EVIDENCE` when total paired delta log < 0 and more than half of Bear divergence epochs favor A;
- otherwise `MIXED_EXTERNAL_MECHANISM_EVIDENCE`.

These labels are retrospective external evidence only; none is prospective validation.

## Leave-one-epoch-out concentration audit

For each Bear divergence epoch, recompute total paired delta with that epoch removed.

- minimum leave-one-epoch-out delta > 0 is reported as `LOEO_ROBUST_POSITIVE`;
- otherwise concentration is reported explicitly as `LOEO_CONCENTRATED_OR_SIGN_UNSTABLE`.

LOEO is a robustness descriptor, not a license to change the rule.

## Secondary absolute-performance reporting

For A and B separately, report at 14bp:

- total return;
- Sharpe (0% risk-free, 15m annualization convention);
- max drawdown;
- turnover/cost;
- Long-only and Short-only core performance;
- yearly chronology;
- campaign count, mean/median campaign log/net result and win rate.

Also report Short initial-entry versus Short re-entry attribution where identifiable. These are descriptive diagnostics, not model-selection criteria.

## Invariants

A valid run requires zero failures for at least:

- Major direction is identical between A and B;
- Candidate B never creates extra Short exposure relative to A;
- Long core occupancy is identical;
- all A/B core divergence is A Short vs B Flat only;
- no direct Long↔Short flip;
- no same-timestamp hard exit plus executed re-entry;
- Bitstamp values never enter PnL;
- no future/backfilled data is used.

Any invariant failure invalidates the performance output until fixed without reference to performance sign.

## Interpretation lock

Even a strong BTC result cannot establish deployable Alpha. BTC tests the frozen mechanism on older regimes; ETH tests cross-asset replication. v0.22 HOLDOUT FAIL remains immutable, and v0.24 remains `INSUFFICIENT_FORWARD_EVIDENCE` until its prospective gate is met.

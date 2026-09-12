# Cross-Exchange Execution Robustness — Frozen Protocol

**Frozen:** 2026-09-12, before downloading or reading Coinbase 2017–2022 execution results in this research stage.

**Classification:** `CROSS_EXCHANGE_EXECUTION_ROBUSTNESS_NOT_PROSPECTIVE`

## Purpose

Test whether the already-frozen Candidate A/B mechanism conclusion is materially dependent on the Binance execution/PnL venue. This is a venue-robustness test only. It does **not** change the strategy signal source and it does not create prospective evidence.

## Frozen decisions

- Candidate A and Candidate B state/action timelines remain exactly those produced by implementation-compatibility v3 from the already-frozen Binance/Bitstamp research inputs.
- No indicator, threshold, state authority, Candidate B permission, sizing rule, cost, or segment rule may change because of Coinbase results.
- BTC and ETH are both evaluated with the same protocol.

## Independent execution venue

- Coinbase Exchange public candles.
- BTC product: `BTC-USD`.
- ETH product: `ETH-USD`.
- Native execution/PnL clock: 15 minutes.
- Target historical window: 2017-08-17 through 2022-12-31, subject to actual Coinbase listing/data availability.

## Causal mapping

- A state decision is usable only after its frozen decision timestamp.
- A decision may fill no earlier than the **next observed Coinbase 15m open** after the decision is known.
- Across missing Coinbase bars or venue gaps, the old exposure remains active until the next observed Coinbase open.
- No Coinbase future bar may backfill an earlier decision.

## Costs

- Primary: 14bp round trip, implemented as 7bp per unit of one-way turnover.
- Secondary frozen stress: +2bp and +5bp one-way slippage, giving total one-way costs of 9bp and 12bp.
- Coinbase prices are used only for this cross-exchange execution/PnL robustness test; they do not feed back into signal/state generation.

## Candidate A/B comparison

The same admissible core difference remains:

- Candidate A = `CORE_SHORT`;
- Candidate B = `FLAT`.

Any other executed A/B authority divergence invalidates the run.

Paired divergence segments are defined from the **executed Coinbase exposures** and include the convergence bar so turnover is charged consistently.

Continuous Major Bear epochs from the frozen decision timeline remain the independent replication unit.

## Evidence floor and labels

Use the same pre-existing external mechanism floor and directional labels:

- >=180 calendar days of eligible history;
- >=6 paired divergence segments;
- >=3 independent Major Bear divergence epochs.

If eligible:

- `EXTERNAL_MECHANISM_SUPPORT` when total paired delta log > 0 and at least two-thirds of Bear divergence epochs favor B;
- `ADVERSE_EXTERNAL_MECHANISM_EVIDENCE` when total paired delta log < 0 and more than half of Bear divergence epochs favor A;
- otherwise `MIXED_EXTERNAL_MECHANISM_EVIDENCE`.

These labels remain retrospective robustness descriptors, not prospective validation.

## Pre-registered venue-consistency interpretation

For each asset:

- `VENUE_CONSISTENT` if Coinbase has the same directional frozen-rule label as the already-recorded Binance execution result;
- `VENUE_SENSITIVE` if the directional label differs;
- `VENUE_EVIDENCE_INSUFFICIENT` if the data/evidence floor is not met.

Known Binance reference labels are locked before Coinbase result inspection:

- BTC: `ADVERSE_EXTERNAL_MECHANISM_EVIDENCE`;
- ETH: `EXTERNAL_MECHANISM_SUPPORT`.

No pooled BTC+ETH pass/fail rule will be invented after seeing Coinbase results.

## Data integrity gate

Before any performance is read, Coinbase data must pass:

- timestamps parse as UTC and are monotonic after sorting;
- duplicate open timestamps are removed deterministically and final duplicates equal zero;
- OHLC envelope consistency;
- positive prices;
- timestamps lie within the requested source period;
- raw response provenance and normalized SHA-256 hashes are recorded;
- missing-bar counts/gaps are reported rather than silently filled.

If integrity fails, performance is invalid until fixed without reference to performance sign.

## Interpretation lock

Cross-exchange agreement can increase confidence that a historical mechanism result is not an artifact of one execution venue, but it cannot validate Candidate B, cannot erase v0.22 HOLDOUT FAIL, and cannot count toward v0.24 prospective evidence.

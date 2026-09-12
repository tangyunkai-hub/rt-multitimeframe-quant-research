# External Validation Data-Method Amendment — Canonical Lower-Timeframe Chain

**Frozen:** 2026-09-12  
**Applies to:** 2017–2022 BTCUSDT primary external historical validation and ETHUSDT cross-asset mechanism replication  
**Evidence label remains:** `EXTERNAL_HISTORICAL_VALIDATION_NOT_PROSPECTIVE`

## Why this amendment exists

The original preregistration treated exact parity between Binance official 15m reconstruction and Binance official native 2h/8h/3d archives as a hard eligibility gate.

Before any 2017–2022 strategy performance was inspected, the source audit established that this assumption is false for a small set of old archive intervals. All Binance monthly files passed their official `.CHECKSUM` verification and the normalized files had no duplicate timestamps, monotonicity failures, or OHLC-envelope failures, yet a small number of official native 2h/8h bars disagreed with aggregation of official lower-timeframe data. An additional forensic pass rebuilt affected intervals from official Binance 1m archives. The 1m reconstruction did **not** remove the native 2h/8h disagreements. The discrepancy is therefore a cross-timeframe archive/version inconsistency, not evidence that one specific lower-timeframe file is corrupt.

This amendment is made from data provenance evidence only. No external-validation strategy return, Sharpe ratio, drawdown, campaign result, Candidate A/B delta, or Bear/Bull epoch result has been read or used to choose this policy.

## Frozen canonical-source rule

For Binance BTCUSDT and ETHUSDT:

1. Official checksum-verified **15m** archives are the canonical execution and Binance feature-construction chain.
2. Binance 2h, 8h and 3d/72h native archives are retained as **diagnostic reference products**, not competing sources that can veto the canonical chain.
3. Binance 2h/8h/72h feature bars are constructed causally from canonical 15m observations using UTC epoch-aligned windows and closed-bar availability.
4. No lower-timeframe price is interpolated, forward-filled, backfilled, or synthetically created.
5. Official 1m data used in the forensic reconciliation remains audit evidence only. It does not silently replace the checksum-verified 15m primary chain.
6. Bitstamp BTCUSD/ETHUSD 12h/1d remain state-confirmation inputs only; their absolute prices are never mixed into Binance PnL.

## Frozen maintenance and irregular-bar rule

A derived Binance 2h/8h/72h feature window is **VALID** only when all of the following hold:

- it contains exactly the expected number of canonical 15m observations: 8 / 32 / 288 respectively;
- every contributing 15m open timestamp lies on the UTC 15-minute grid;
- the canonical 15m source itself passes duplicate, monotonicity, and OHLC-envelope integrity checks.

Otherwise the derived feature window is **QUARANTINED / INVALID**.

For an invalid derived feature window:

- no new signal/event is emitted from that timeframe;
- the last already-confirmed state persists according to the frozen state-machine invariant;
- no synthetic candle is created;
- execution/PnL continues only across actually observed canonical Binance bars, so an exchange-maintenance gap remains a real untradeable gap rather than a fabricated continuous market.

This treatment is deterministic and is based only on timestamps/source completeness, never on future returns or whether excluding a window improves strategy performance.

## Revised data gates

### Hard source-integrity gate

Strategy evaluation is blocked if any required source has:

- failed Binance official checksum verification;
- a missing post-listing monthly archive;
- duplicate timestamps;
- non-monotonic timestamps;
- OHLC-envelope violations;
- an unreadable/invalid normalized file or missing required state-confirmation source.

### Canonical feature-eligibility gate

The canonical 15m chain must successfully produce a deterministic validity mask for 2h/8h/72h windows. Invalid windows are permitted only because they are explicitly quarantined before strategy evaluation.

### Native higher-timeframe parity diagnostic

Official native 2h/8h/3d parity remains reported in full, including every mismatch timestamp and magnitude, but is **not a hard eligibility criterion** because official Binance products were empirically shown to disagree with each other in old history.

## Pre-frozen source-sensitivity requirement

After the canonical-chain primary result is produced, a separate source-sensitivity diagnostic may compare conclusions against native Binance higher-timeframe inputs where technically valid. This diagnostic cannot replace, select, or optimize the primary result. Any material conclusion change must be reported as data-source fragility.

## Anti-overfit rule remains unchanged

Candidate A/B semantics, thresholds, role authority, transaction-cost convention and sizing are unchanged. No 2017–2022 result may be used to retune Candidate B. If these data contradict Candidate B, the contradiction is retained. Any new response becomes a separately versioned hypothesis with a new freeze boundary.

## Interpretation limit

Passing the amended gate permits **historical external validation only**. It does not make Candidate B prospectively validated and does not alter:

- v0.22 `HOLDOUT_FAIL_NOT_DEPLOYMENT_READY`;
- Candidate B `FROZEN_HYPOTHESIS_NOT_VALIDATED`;
- v0.24 `INSUFFICIENT_FORWARD_EVIDENCE`.

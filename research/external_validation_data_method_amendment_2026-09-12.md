# External Validation Data-Method Amendment — Canonical Lower-Timeframe Chain

**Frozen:** 2026-09-12  
**Applies to:** 2017–2022 BTCUSDT primary external historical validation and ETHUSDT cross-asset mechanism replication  
**Evidence label remains:** `EXTERNAL_HISTORICAL_VALIDATION_NOT_PROSPECTIVE`

## Why this amendment exists

The original preregistration treated exact parity between Binance official 15m reconstruction and Binance official native 2h/8h/3d archives as a hard eligibility gate.

Before any 2017–2022 strategy performance was inspected, the source audit established that this assumption is false for a small set of old archive intervals. All Binance monthly files passed their official `.CHECKSUM` verification and the normalized files had no duplicate timestamps, monotonicity failures, or OHLC-envelope failures, yet a small number of official native 2h/8h bars disagreed with aggregation of official lower-timeframe data. A forensic pass rebuilt affected intervals from official Binance 1m archives and did **not** remove those native 2h/8h disagreements. The discrepancy is therefore a cross-timeframe archive/version inconsistency, not evidence that one specific lower-timeframe file is corrupt.

A second pre-performance audit showed that BTCUSDT and ETHUSDT have the same 31 historical 15m cadence interruptions (29 exact timestamp matches; the two February-2018 restart boundaries differ only by the exchange-recorded millisecond suffix) and both contain the same 81 off-grid restart bars. This cross-asset coincidence is consistent with exchange-wide maintenance/restart history rather than isolated symbol-file corruption.

No external-validation strategy return, Sharpe ratio, drawdown, campaign result, Candidate A/B delta, or Bear/Bull epoch result had been read when this policy was frozen.

## Frozen canonical-source rule

For Binance BTCUSDT and ETHUSDT:

1. Official checksum-verified **15m** archives are the canonical execution and Binance feature-construction chain.
2. Binance native 2h, 8h and 3d/72h archives are retained as **diagnostic reference products**, not competing sources that can veto the canonical chain.
3. Every Binance-derived strategy timeframe is constructed causally from canonical 15m observations using the frozen wall-clock alignment and closed-bar availability: **30m, 1h, 2h, 4h, 8h, 12h, 1d, 72h and weekly authority**.
4. No lower-timeframe price is interpolated, forward-filled, backfilled, or synthetically created.
5. Official 1m data used in the forensic reconciliation remains audit evidence only and does not silently replace the checksum-verified 15m primary chain.
6. Bitstamp BTCUSD/ETHUSD 12h/1d remain state-confirmation inputs only; their absolute prices are never mixed into Binance PnL.

## Frozen maintenance and irregular-bar rule

A missing 15m interval during an exchange-wide maintenance halt is **not** treated as a synthetic-data invitation and is **not** by itself grounds to discard the containing higher-timeframe candle. The canonical higher-timeframe OHLC is aggregated from the observations that actually existed. The gap is logged and remains an untradeable wall-clock gap; no price is invented inside it.

A derived Binance feature candle is **QUARANTINED / INVALID** only when one or more contributing 15m observations are **off the standard UTC 15-minute grid**, because assigning such restart bars to fixed wall-clock strategy candles is ambiguous. A quarantined candle is excluded **before indicator computation**, cannot emit a new signal, and cannot alter later indicator state indirectly. The last already-confirmed strategy state persists until a valid new event appears.

Thus:

- cadence-count deficiency = audit flag, but not automatic invalidation;
- off-grid input = invalid/quarantined feature candle;
- source duplicate, non-monotonicity, OHLC-envelope failure, checksum failure, or missing post-listing monthly archive = hard failure.

This distinction is deterministic and based only on source/timestamp structure, never on future returns or whether a treatment improves performance.

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

The canonical 15m chain must produce a deterministic audit ledger for every Binance-derived strategy timeframe. Gap-crossing candles are reported. Candles containing off-grid inputs are quarantined before indicator calculation and strategy evaluation.

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

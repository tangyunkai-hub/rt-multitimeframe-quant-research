# Historical External Validation Program — Preregistration

**Frozen on:** 2026-09-12  
**Purpose:** increase evidence outside the already-consumed 2023–2026 development/holdout history without mislabeling retrospective data as prospective evidence.

> **Data-method amendment, frozen before external performance inspection:** `research/external_validation_data_method_amendment_2026-09-12.md`. The amendment changes native Binance higher-timeframe parity from a hard gate to a diagnostic after official 1m/15m/native archives were shown to disagree in a small number of old intervals. The canonical execution/feature chain is checksum-verified Binance 15m with deterministic quarantine of incomplete/off-grid derived windows. Strategy semantics and anti-overfit rules are unchanged.

## Evidence classification

This program is classified as **EXTERNAL_HISTORICAL_VALIDATION_NOT_PROSPECTIVE**.

The 2017–2022 datasets were not used in the current Candidate B performance evaluation. They are therefore useful external historical evidence, but they are still retrospective market history and must not be described as forward or live validation.

## Frozen datasets

### Primary old-history BTC validation

- Binance Spot **BTCUSDT**
- period: 2017-01-01 through 2022-12-31, subject to actual listing availability
- base/execution reconstruction: native **15m** archives
- native parity references: **2h, 8h, 3d**
- Bitstamp **BTCUSD**: **12h and 1d**, state-confirmation data only

### Cross-asset validation

- Binance Spot **ETHUSDT**
- same period and intervals
- Bitstamp **ETHUSD**: **12h and 1d**, state-confirmation data only

## Data provenance

1. Binance data must come from official `data.binance.vision` monthly Spot Kline archives.
2. Every downloaded Binance archive must pass its official SHA-256 `.CHECKSUM` file.
3. Bitstamp data must come from the official public API v2 OHLC endpoint.
4. Every Bitstamp HTTP payload is hashed and logged in the request manifest.
5. BTCUSD/ETHUSD higher-timeframe prices are state inputs only and are never mixed into Binance PnL.

## Data gates

Before any strategy evaluation:

- timestamp monotonicity;
- duplicate-timestamp audit;
- OHLC envelope audit;
- cadence/gap report;
- canonical 15m-derived 2h/8h/72h feature-window validity mask;
- native 2h/8h/3d Binance parity retained as a diagnostic rather than an eligibility veto, per the frozen amendment;
- source URL/hash manifest;
- normalized output hashes.

Any hard source-integrity failure blocks strategy evaluation. Incomplete or off-grid derived higher-timeframe windows are deterministically quarantined and cannot emit new signals.

## Frozen strategy rule

Candidate A and Candidate B semantics, indicator thresholds, transaction-cost convention and role authority are frozen before viewing external-validation performance.

**No result from 2017–2022 BTC or ETH may be used to tune Candidate B.**

If the external history contradicts Candidate B, the contradiction is retained. Any new semantic response becomes a separately versioned Candidate C with a new freeze boundary and may not be evaluated as validated on the same data that suggested it.

## Interpretation

The external program asks two questions:

1. Does the already-frozen architecture reproduce its intended causal/state behavior on an older BTC market regime?
2. Does the Candidate A/B mechanism generalize directionally to a second liquid crypto asset without changing the rule?

Positive evidence strengthens the case for a real mechanism but does not replace the prospective v0.24 gate. Negative evidence weakens the Alpha hypothesis immediately and must not be hidden.

## Existing evidence remains immutable

- v0.22 frozen holdout: **FAIL**
- Candidate B: **FROZEN_HYPOTHESIS_NOT_VALIDATED**
- prospective status: **INSUFFICIENT_FORWARD_EVIDENCE**

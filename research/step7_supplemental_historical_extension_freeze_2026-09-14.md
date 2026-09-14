# RT Quant Research — Step 7 Supplemental Historical Extension Freeze

Date: 2026-09-14
Status: FROZEN_BEFORE_NEW_SUPPLEMENTAL_SOURCE_OUTCOME_READ
Validated Alpha at freeze: NO

Purpose: continue productive retrospective robustness research while PRIMARY prospective evidence matures, without reopening/retuning closed Major Steps 3–6 and without contaminating Step 7 prospective evidence.

Frozen PRIMARY sleeves transported unchanged:
1. C2_W1_02_LONG_PRIMARY
2. C3_W2_LONG_PRIMARY
3. C3_W2_SHORT_PRIMARY

Excluded: C6 duplicate lineage, C4/L01, C5, C1, Candidate B, new weights, parameter grids, threshold changes, holding-period changes, result-driven sleeve deletion.

Frozen execution semantics: next observed 15m open; fixed 2 calendar days; 7 bp one-way entry/exit cost; CAP_ONE__IGNORE_WHILE_ACTIVE; EXTRA_0M; 1x; equal-initial-thirds/no-rebalance descriptive reference only when all sleeves executable; no synthetic interpolation.

Wave H1 — Binance Spot ETHUSDT 15m official archive, 2023-01-01T00:00:00Z <= open_time < 2026-09-01T00:00:00Z. Natural non-overlapping continuation after the already-consumed ETH 2017–2022 block.

Wave H2 — Bitfinex official 15m trade candles for tBTCUSD and tETHUSD. Lower bound = first official candle; upper bound open_time < 2017-08-17T00:00:00Z. Same-venue signal generation/execution.

Wave H3 — Kraken official downloadable OHLCVT archive, 15m BTC/USD and ETH/USD equivalents. Lower bound = first official candle; upper bound open_time < 2017-08-17T00:00:00Z. Same-venue signal generation/execution.

Before any performance read, source gate requires immutable request/source manifest, source and normalized hashes where available, monotonic timestamps, no duplicate timestamps after source-faithful exact de-duplication, OHLC envelope validity, explicit preserved gap inventory, availability_time=open_time+15m, and no rows at/after the frozen endpoint.

Compatibility must be proven before performance: the unchanged strategy implementation must reproduce the already-consumed regression substrate. Outcome-blind parser/source hardening is allowed only if regression-neutral.

All three waves must be reported including adverse, sparse, blocked, inactive, or null evidence. No pooled post-hoc pass/fail. This evidence is retrospective, never prospective. The immutable PRIMARY prospective start remains 2026-09-14T08:45:00Z and H1/H2/H3 may not enter prospective ledgers or maturity counters.

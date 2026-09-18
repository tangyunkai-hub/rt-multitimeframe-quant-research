# Broad Discovery Cycle-2 — Funding Source Audit

Frozen 2026-09-18 before any Cycle-2 performance read.

## Scope
Source-only audit for Binance BTCUSDT USD-M perpetual funding history supporting the already-frozen Cycle-2 funding/carry family. No candidate return, Sharpe, drawdown, selection, or tuning was computed/read in this audit.

## First-party connector observation
A direct Binance USD-M funding-history query over the launch-era interval 2019-09-10 through 2019-12-31 returned native BTCUSDT funding observations in ascending time order. The first observed record is 2019-09-10 08:00:00 UTC (1568102400000). Launch-era observations are approximately 8-hourly, with occasional millisecond timestamp offsets; rates are not assumed constant and later observations include both positive and negative values.

The source is therefore adequate in principle for the frozen F1/F2/F3 mechanisms beginning after their required causal lookback. No missing funding payment will be fabricated. Calendar-day funding sums must use only native observations actually returned by the source through the UTC day close.

## Governance implications
- Funding family remains development-only on the already-consumed Binance BTCUSDT USD-M substrate.
- This audit does not authorize use of Kraken V2b, GC, equity-index, or any reserved/transport data.
- F1/F2/F3 formulas remain exactly as frozen in `CYCLE2_IMPLEMENTATION_FREEZE_20260918.md`; no thresholds/lookbacks were changed after seeing source values.
- Before the first Cycle-2 performance read, the exact normalized funding payload/manifest used by the runner and the exact runner bytes must be durably persisted and hashed.
- All 12 Cycle-2 candidate outcomes must be retained; at most one representative per family may advance.
- `Validated Alpha = NO`.

## Exact next data-engineering action
Acquire the full frozen development-window BTCUSDT funding history in deterministic ascending pages; canonicalize fields `(symbol,fundingTime,fundingRate,rateType)` without interpolation; audit duplicates/order/coverage; persist bytes + SHA256. Separately persist the exact Cycle-2 runner + SHA256 before execution. Premium-index coverage remains later-starting and must retain coverage-aware evaluation.
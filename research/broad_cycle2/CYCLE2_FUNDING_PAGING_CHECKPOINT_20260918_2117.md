# Broad Discovery Cycle-2 — Funding paging checkpoint

Date: 2026-09-18 21:17 CST
Status: DATA ENGINEERING ONLY / NO PERFORMANCE READ

Continued from authoritative Master Handoff `(13)` exact-next-task boundary.

## Governance
- No Cycle-2 candidate signal, return, Sharpe, drawdown, or promotion result was computed/read.
- Frozen F1/F2/F3 formulas, thresholds, execution, costs, scoring and promotion rules are unchanged.
- Missing funding observations will not be interpolated or fabricated.
- Full canonical payload + manifest + SHA256 and exact runner bytes + SHA256 must still be durably frozen before the first Cycle-2 outcome.

## Deterministic paging progress
Using the connected first-party Binance USD-M funding-history endpoint for `BTCUSDT`, deterministic chronological paging was advanced from the native launch-era start.

- Page 1 begins: `2019-09-10 08:00:00 UTC` (`fundingTime=1568102400000`).
- Page 1 ends: `2020-08-08 00:00:00 UTC` (`fundingTime=1596873600000`).
- Page 2 begins strictly after that timestamp: `2020-08-08 08:00:00 UTC` (`fundingTime=1596902400000`).
- Page 2 ends: `2021-07-07 16:00:00.008 UTC` (`fundingTime=1625673600008`).
- The returned sequence remains approximately 8-hourly, with the already-observed occasional millisecond timestamp offsets and both positive/negative funding states.

This checkpoint intentionally does **not** claim the full-development payload is complete and does not assign a final payload SHA. It exists only to make pagination progress durable across bounded automation runs.

## Exact continuation
Resume with `startTime=1625673600009` through the frozen development cutoff, page chronologically to completion, then canonicalize `(symbol,fundingTime,fundingRate,rateType)`, audit ordering/duplicates/coverage, persist the complete payload + manifest + SHA256. Acquire/freeze premium-index payload similarly. Persist exact Cycle-2 runner + SHA256 BEFORE the single retained 12-candidate batch. Kraken V2b remains unconsumed; GC remains frozen; `Validated Alpha = NO`.

# Broad Discovery Cycle-1 — V1 Pre-2019 BTC Spot Source Freeze

Date: 2026-09-18
Status: FROZEN BEFORE ANY V1 CANDIDATE PERFORMANCE READ
Parent research state: RT_QUANT_MASTER_HANDOFF_CURRENT_2026-09-18(6)

## Purpose
Acquire and audit a durable BTC/USD spot daily dataset strictly before 2019-09-08 for independent-time Validation Gate V1 of the already-frozen representatives TSMOM_120 and VM_TSMOM20. This phase is source engineering only. No candidate signal, position, return, Sharpe, drawdown, win rate, or performance diagnostic may be calculated/read until the source manifest and implementation mapping are frozen.

## Primary source
Bitstamp public REST OHLC endpoint for BTC/USD (`btcusd`), step=86400, exclude_current_candle=true. The official API documents start/end timestamps and daily step support. Use only completed daily candles.

## Frozen V1 interval
- Upper bound: timestamps strictly before 2019-09-08T00:00:00Z.
- Lower bound: earliest durable BTC/USD daily candle actually returned by the primary source, with no discretionary truncation after inspection.
- If source pagination requires chunks, concatenate chronologically and deduplicate by UTC candle timestamp.

## Frozen source gates
Before any strategy calculation:
1. Persist raw normalized daily OHLCV rows.
2. Record retrieval timestamp, endpoint/market, requested bounds, observed first/last timestamps, row count and source provenance.
3. Require unique strictly increasing timestamps.
4. Record all missing UTC calendar-day intervals; do not synthesize/interpolate missing bars.
5. Require positive O/H/L/C and valid OHLC envelope (`low <= min(open,close) <= max(open,close) <= high`).
6. SHA256 hash the normalized dataset and source manifest.
7. Freeze exact spot-to-frozen-runner column/timestamp mapping before candidate performance.

## Frozen candidate semantics
Only the already-promoted Cycle-1 representatives may be evaluated in the first V1 batch:
- TSMOM_120
- VM_TSMOM20
No parameter, horizon, volatility estimator, target, execution timing, turnover/cost rule, scoring hierarchy, or candidate membership may change from the Cycle-1 implementation freeze. Both outcomes must be retained.

## Validation interpretation
V1 is independent-time BTC spot transport. It is not same-instrument continuity: development used Binance BTCUSDT USD-M perpetual from 2019-09-08 onward, while V1 uses earlier BTC/USD spot history. Therefore instrument/venue/basis differences are part of transport stress and must not be repaired after outcome inspection.

## Failure policy
If Bitstamp cannot provide a sufficiently durable pre-2019 history, acquire another lawful public BTC/USD spot source under a new source-only addendum before any candidate performance. Do not weaken the date boundary, use post-2019 data, or tune the candidates.

Validated Alpha remains NO.
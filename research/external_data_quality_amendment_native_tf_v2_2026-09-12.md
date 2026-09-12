# External Historical Validation — Data Quality Amendment v2

Date: 2026-09-12

Classification: `EXTERNAL_HISTORICAL_VALIDATION_NOT_PROSPECTIVE`

## Why this amendment exists

The original external-history data gate required OHLC bars reconstructed from Binance 15m archives to match separately published Binance native 2h/8h/3d archives exactly. That gate failed **before any external strategy-performance result was inspected**.

The failure is preserved and is not re-labelled as a pass.

Audit work identified two source-data semantics that make exact cross-granularity reconstruction an invalid universal requirement for old Binance archives:

1. Early archives contain zero-trade placeholder candles. A lower-timeframe placeholder can carry a stale price even though the native higher-timeframe candle opens at the first actual trade. When zero-trade candles are excluded from OHLC first/last selection, most early mismatches disappear exactly.
2. Exchange maintenance/restart periods contain non-standard candle anchors (for example, bars beginning at offsets such as `:58:14.xxx`) while another native timeframe may remain anchored to normal UTC boundaries. Separately published native archives therefore cannot always be recreated exactly from a different archived granularity, even when both are official and checksum-valid.

A second official 1m reconstruction test also failed to resolve every old cross-granularity difference. This supports the conclusion that the remaining mismatch is an archive-granularity issue rather than a missing-15m-only issue.

## Frozen v2 data rule

This amendment changes **data representation only**, not trading semantics, thresholds, costs, sizing, or evaluation criteria.

For external historical evaluation:

- Binance 15m remains the execution/PnL clock.
- Every Binance signal timeframe is read from its own official native archive: 30m, 1h, 2h, 4h, 8h, 12h, 1d, 3d, and 1w.
- Bitstamp 12h/1d remains a state-confirmation source only where the research architecture already requires it.
- Cross-timeframe OHLC equality is recorded as a diagnostic, not used as a universal hard gate.
- Each native archive must independently pass checksum verification, timestamp uniqueness/monotonicity, and OHLC-envelope integrity.
- Exchange outages and non-standard historical anchors are retained as observed; no interpolation or synthetic price bars are inserted.
- Closed-bar availability remains `native open_time + native timeframe duration`.
- No future information may be backfilled across gaps.

## Anti-overfit lock

This amendment was specified from source-data diagnostics only, before reading 2017–2022 strategy performance. External historical results may not be used to alter strategy semantics, thresholds, transaction-cost assumptions, risk sizing, or this data rule.

Before external performance is read, the native-timeframe adapter must pass a regression test on the already-consumed modern sample. Any material state/action mismatch requires explanation and blocks external evaluation.

## Evidence status

The original strict reconstruction gate remains: `FAIL`.

The v2 native-timeframe path is a separately versioned data adapter and must earn its own integrity and regression gates before strategy evaluation becomes eligible.

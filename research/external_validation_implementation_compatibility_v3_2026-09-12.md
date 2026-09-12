# External Historical Validation — Implementation-Compatibility Amendment v3

**Frozen:** 2026-09-12, before any 2017–2022 Candidate A/B strategy-performance result was read.

**Classification:** `EXTERNAL_HISTORICAL_VALIDATION_NOT_PROSPECTIVE`

## Why v3 is required

The native-timeframe-v2 dataset passed independent source-integrity checks, but its modern-sample state/action regression against the already-consumed Candidate A/B implementation produced material authority-critical differences. In particular, native exchange 3D/weekly archive anchoring does not reproduce the calendar/bar semantics used by the frozen research implementation and by the saved TradingView evidence. Therefore:

- the v1 exact cross-granularity reconstruction gate remains preserved as `FAIL`;
- native-timeframe-v2 source integrity remains `PASS`;
- native-timeframe-v2 **Candidate A/B semantic compatibility is `FAIL`**;
- no 2017–2022 strategy performance may be read through native-timeframe-v2.

This amendment does not repair, improve, or reinterpret Candidate A/B. It freezes an adapter whose purpose is to evaluate the **already-frozen implementation as it actually existed**.

## Frozen implementation-compatible external adapter

### 1. Execution and PnL clock

- Official checksum-verified Binance Spot 15m archives remain the only execution/PnL price clock.
- Source timestamps are retained as observed, including exchange-maintenance/restart offsets.
- No interpolation, timestamp snapping, synthetic candles, or future backfill is allowed.

### 2. Candidate A/B core feature path

For the core Candidate A/B feature/regime path, apply the same causal 15m-to-higher-timeframe aggregation implementation used by the consumed pre-holdout research code:

- input index is closed/available 15m time;
- fixed-timeframe aggregation is right-closed, right-labeled, epoch-origin;
- the same frozen indicator implementation and thresholds are used;
- the same persistent Major-regime state machine and W2/W1 sequencing/permission logic are used.

This path is intentionally implementation-compatible. It is **not** replaced by official native higher-timeframe archives when doing so changes authority-critical state/action semantics.

### 3. Higher-overlay sources that were native in the frozen implementation

The frozen implementation used separate native-style higher-overlay semantics. Those are reconstructed externally without changing their role:

- **W7 3D overlay:** reconstruct TradingView-compatible 3D calendar bars causally from checksum-verified Binance 15m OPEN timestamps, with each calendar year starting a new Jan-1 + 3-day sequence. Modern saved TradingView evidence showed zero OHLC and TDO/SSL state/event mismatches on the comparison sample.
- **W7 weekly process:** reconstruct Monday-open crypto weeks `[Mon 00:00, next Mon 00:00)` from Binance 15m OPEN timestamps and label availability at the next Monday. Modern saved TradingView evidence showed exact weekly TDO parity on the audited sample.
- **W3 12h / W8 1d Bitstamp state source:** use official Bitstamp API OHLC and the frozen indicator implementation. On the modern pre-holdout overlap (2023-06-01 through 2026-01-10 07:00 UTC), official API versus saved native TradingView produced zero authority-event/state mismatches for 12h SSL state/up/down and 1d TDO GC/DC/oversold state after causal warm-up.

A small raw-OHLC source discrepancy that does not alter any frozen authority event/state is retained in the audit and is not hidden.

### 4. Intentional dual 3D semantics

The consumed Candidate A/B implementation already had two distinct 3D roles:

1. the **Major-regime 3D** feature belongs to the core 15m-derived implementation path;
2. the **W7 overlay 3D** belonged to the native TradingView higher-overlay path.

v3 preserves this distinction exactly. Collapsing them into one "cleaner" 3D clock would change the model and would therefore define a new candidate, not validate Candidate B.

## Anti-overfit lock

- No 2017–2022 BTC or ETH performance result may alter this adapter, Candidate B semantics, thresholds, costs, sizing, or evaluation criteria.
- If implementation-compatible external results are poor, the poor result is retained.
- Any later corrected/unified calendar model is a separately versioned Candidate C (or later) with a new freeze boundary and cannot claim validation on the same history that motivated it.
- Bitstamp prices remain state-only and are never mixed into Binance PnL.

## Eligibility consequence

External performance remains blocked until the implementation-compatible adapter itself passes its modern-sample state/action regression and invariant audit. Only then may the frozen BTC 2017–2022 Candidate A/B evaluation run, followed by the separately frozen ETH replication.

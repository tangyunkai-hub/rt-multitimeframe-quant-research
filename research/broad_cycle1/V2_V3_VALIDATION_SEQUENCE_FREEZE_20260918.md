# Broad Discovery Cycle-1 — V2/V3 Validation Sequence Freeze

Date: 2026-09-18
Status: FROZEN BEFORE ANY V2/V3 OUTCOME READ
Parent evidence: Cycle-1 consumed Binance BTCUSDT USD-M 1D development; V1 independent-time Bitstamp BTC/USD 2012-01-01..2019-09-07 supportive.
Candidates (immutable): TSMOM_120 and VM_TSMOM20. They share trend ancestry and count as one broad trend-family discovery.

## Governance
No parameter, signal, execution, cost, volatility-target, horizon, threshold, or candidate-selection change is authorized after V1. All outcomes retained. V2 is replication evidence, NOT independent-time evidence. V3 is unchanged cross-asset transport. No V2/V3 result may feed back into this lineage.

## V2 — same-calendar alternative-venue BTC replication
Primary source is the already-acquired Coinbase BTC-USD 15m data-only artifact from workflow run 34699255006, artifact 10299497700, ZIP SHA256 8fc7692bd5497a154be6867f79388fde9943ecb7d70ed8b8607b9c3f61403d42, normalized BTC-USD SHA256 prefix bd77a2d1. This source was acquired for prior cross-venue diagnostics before Cycle-1 trend outcomes and therefore is not selected based on current candidate performance.

Frozen overlap: intersection of Coinbase complete source coverage and Cycle-1 development calendar, beginning 2019-09-08 and ending at the last complete UTC day strictly before Coinbase final availability 2023-01-01T00:00:00Z; expected terminal daily date 2022-12-31, subject to source audit only.

Mapping: aggregate source-faithful Coinbase 15m OHLCV causally to UTC calendar daily bars: open=first observed open, high=max high, low=min low, close=last observed close, volume=sum observed volume. Do not interpolate missing 15m bars. A daily bar is admissible if at least one native observation exists; gap counts are reported. Signal and next-daily-open execution semantics, baseline 7bp/side, 28bp and 56bp round-trip stress, TSMOM_120 definition, and VM_TSMOM20 volatility estimator/notional-turnover cost semantics remain exactly as frozen in Cycle-1. First 120/20 lookback observations are naturally unavailable as in the runner. No source-driven truncation except coverage intersection.

Pre-performance gates: exact artifact/source hash match; monotonic unique timestamps; duplicate inventory; nonpositive/OHLC-envelope checks; native-gap inventory; daily normalized SHA256; exact runner SHA256; deterministic rerun. If source artifact cannot be recovered exactly, V2 remains blocked until a source addendum is frozen BEFORE outcomes; do not substitute a venue after seeing performance.

Interpretation: compare sign, compounding, Sharpe, MaxDD, turnover, cost stress and calendar subperiod breadth to Binance. Do not require magnitude equality. V2 cannot upgrade evidence to independent-time OOS.

## V3 — unchanged cross-asset transport sequence
V3 source/performance embargo remains until each source/mapping freeze is written before its first outcome. Sequence is frozen as:
1. exact COMEX Gold futures (GC) if durable exact outright-contract payload becomes available under the already-frozen GC roll/session/execution semantics;
2. broad US equity-index transport using an audited broad-market futures series where exact durable data are available; if futures are unavailable, a separately labeled ETF-proxy transport may use SPY only after source/mapping freeze and must not be called futures evidence;
3. additional broad equity-index / diversified liquid assets only after the first V3 leg, under separately frozen source manifests;
4. suitable individual equities only after index-level transport.

No GC=F or undocumented synthetic continuous gold substitute is authorized for exact GC transport. Existing SOURCE-ONLY equity-index data remain embargoed from performance until source/mapping freeze.

## Decision rule
Trend family remains a serious historical candidate only if evidence is not dominated by one venue/era and unchanged transport shows economically coherent breadth. VM_TSMOM20's lower drawdown is descriptive evidence, not authorization to drop TSMOM_120 before the frozen validation stack is complete. Validated Alpha remains NO until governance formally changes it.

# Cycle-2 V1-V1 Bitstamp Independent-Time Validation Result — 2026-09-19

## Governance
- Protocol frozen before outcome: `V1_VALIDATION_PROTOCOL_FREEZE_20260919.md`.
- Source binding frozen before outcome: Bitstamp BTC/USD daily, 2012-01-01..2019-09-07, 2,807 rows, normalized SHA256 `3c8d32b1d13a8bf77348c9a04be616b7ba82b4a4553bfe59654260410c5a9e60`.
- Runner frozen before outcome: `run_v1_v1_bitstamp.py`, SHA256 `35caa926b3782600545a787950b4f7e796ae6e4fb10e63982af5eb13871df503`.
- Single retained workflow run: `35418286106`, job `105831043624`, SUCCESS.
- Uploaded artifact ZIP SHA256: `5003ee7d9fff1eff0e1992e87d81dc6d0d14ff0db706d3c44a1f204c79e332f6`.
- No threshold/horizon/direction/sizing/ensemble change was made after outcome.

## Frozen V1 semantics
`VOL_EXPANSION_FLAT`: daily close-to-close log returns; population-standard-deviation RV20/RV60; next day flat only when RV20/RV60 > 1.25, otherwise long. Execution is causal next-UTC-day open-to-open. Baseline friction 7bp/side with retained 28/56bp round-trip-equivalent stress.

## Independent-time result
### V1 baseline
- terminal return: +9,565.52% (`95.6551867` as return multiple over initial capital)
- Sharpe: 1.2102
- MaxDD: -83.66%
- turnover: 87
- invested fraction: 78.13%
- worst daily return: -29.24%

### V1 cost stress
- 28bp RT-equivalent: terminal return +8,993.37%, Sharpe 1.1986, MaxDD -83.89%
- 56bp RT-equivalent: terminal return +7,947.64%, Sharpe 1.1752, MaxDD -84.34%

### Same-market always-long benchmark
- baseline terminal return: +205,936.47%
- Sharpe: 1.5656
- MaxDD: -84.85%
- turnover: 1
- invested fraction: 99.96%
- worst daily return: -48.52%

### Incremental V1 versus always-long
- MaxDD improvement: only +1.183 percentage points
- Sharpe delta: -0.3554
- terminal-return delta: -196,370.95 percentage points
- worst-day loss is materially smaller for V1 (-29.24% vs -48.52%), but this tail-day improvement does not compensate for the very small full-period MaxDD improvement and lower Sharpe under the preregistered benchmark-relative interpretation.

## Classification
`V1_V1_INDEPENDENT_TIME_POSITIVE_ABSOLUTE_RETURN__BENCHMARK_RELATIVE_RISK_CONTROL_WEAK__NOT_PROMOTED_AS_STANDALONE_ALPHA`

This is an important adverse/qualifying result. V1 does produce positive independent-time compounding and remains positive under severe transaction-cost stress, so the development result was not pure sign noise. However, its preregistered role is primarily a volatility-expansion risk-state control. On genuinely independent pre-2019 BTC history it improves full-period MaxDD by only ~1.18pp while reducing Sharpe by ~0.36 and sacrificing the vast majority of always-long terminal compounding. Therefore V1 is not promoted as standalone Alpha or as a validated risk-control component at this stage.

Do not rescue-tune RV20/RV60 or threshold 1.25. Do not ensemble with VM_TSMOM20/TSMOM120 yet. Preserve this adverse evidence.

`Validated Alpha = NO`.

## Exact next research task
1. Preserve V1-V1 as adverse/qualifying independent-time evidence.
2. Continue the already-frozen V1-V2 same-calendar cross-venue lane only as a mechanism replication diagnostic; it cannot overturn the weak independent-time benchmark-relative verdict by itself.
3. Continue Kraken V2b first-party acquisition for the stronger Cycle-1 trend representatives, which remains the higher-priority BTC validation lane.
4. Keep exact GC transport frozen pending durable COMEX outright payload and equity-index data SOURCE-ONLY.
5. No V1/trend ensemble until standalone evidence is complete.
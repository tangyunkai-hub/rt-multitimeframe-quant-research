# Cycle-2 V1-V1 Bitstamp Independent-Time Source Binding

Frozen BEFORE any Cycle-2 V1 outcome is read on this source.

- Candidate: `VOL_EXPANSION_FLAT` exactly as frozen in `V1_VALIDATION_PROTOCOL_FREEZE_20260919.md`.
- Validation lane: V1-V1 genuinely independent-time BTC.
- Source: `alessiostomeo/btc-cycle-data`, path `bitstamp/1day/BTCUSD_bitstamp_daily_2012-2026.csv`, documented source-faithful Bitstamp daily history.
- Evaluation source slice: 2012-01-01 through 2019-09-07 inclusive; 2,807 UTC daily rows; chronologically disjoint from consumed Binance USD-M development starting 2019-09-08.
- Existing audited normalized source identity is reused exactly: SHA256 `3c8d32b1d13a8bf77348c9a04be616b7ba82b4a4553bfe59654260410c5a9e60`; zero calendar gaps, duplicates, nonpositive OHLC, or OHLC-envelope violations.
- Pedigree disclosure: these exact bytes were previously consumed for Cycle-1 trend-candidate outcomes, but no Cycle-2 V1 volatility-regime outcome has been read on them. This is therefore independent-time for V1 outcome evaluation but not a globally untouched dataset.
- Frozen runner path: `research/broad_cycle2/run_v1_v1_bitstamp.py`.
- Frozen runner SHA256: `35caa926b3782600545a787950b4f7e796ae6e4fb10e63982af5eb13871df503`.
- Runner semantics: daily close-to-close log returns; population std (`ddof=0`); RV20/RV60; next-day position flat only when ratio >1.25 else long; next-UTC-day open-to-open execution; baseline 7bp/side turnover friction plus retained 28/56bp round-trip-equivalent stresses; same-market always-long benchmark mandatory.
- No 20/60/1.25 search, direction rule, stop/target, leverage, sizing, ensemble, or bad-period deletion is authorized after this freeze.
- `Validated Alpha = NO` regardless of this single lane outcome.

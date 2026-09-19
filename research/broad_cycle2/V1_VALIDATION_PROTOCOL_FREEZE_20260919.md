# Cycle-2 V1 VOL_EXPANSION_FLAT — Validation Protocol Freeze

Frozen 2026-09-19 after Cycle-2 development triage and BEFORE any new V1 validation/transport performance read.

## Status and purpose
V1 is the sole Cycle-2 family representative eligible for validation. Development evidence is consumed discovery evidence only; it does not establish validated Alpha. `Validated Alpha = NO`.

This protocol preserves V1 exactly and tests whether its apparent benefit is a reproducible volatility-state/risk-control effect rather than a BTC-development-sample accident. No result-driven rescue, threshold search, horizon search, leverage/sizing optimization, stop/target addition, or ensemble with trend candidates is authorized in this validation lineage.

## Frozen V1 definition
Input: daily close-to-close log returns from the relevant asset/venue daily OHLCV.

- `RV20_t = sqrt(A) * population_std(last 20 daily log returns through day t)`
- `RV60_t = sqrt(A) * population_std(last 60 daily log returns through day t)`
- ratio `R_t = RV20_t / RV60_t`
- decision: `position_{t+1} = 0` if `R_t > 1.25`, else `+1`.

`A` is the calendar annualization convention appropriate to the source calendar; for 24/7 crypto use 365. The annualization factor cancels in the ratio and therefore cannot change the state decision. Population standard deviation (`ddof=0`) is frozen. Exactly 20/60 observed daily returns are required; no interpolation of missing source days is permitted. No price-direction sign enters the signal.

Interpretation is frozen as **volatility-expansion risk-state control**. It is not presumed to be standalone directional Alpha. Validation must compare it against the same-market always-long benchmark so that any value can be attributed to avoided expansion states rather than merely long market beta.

## Frozen execution and cost semantics
For crypto daily validation, information through UTC day close `t` determines the position applied to the next observed UTC daily open-to-open return. Causal next-day execution only; no lookahead or same-close fill. Baseline friction is 7 bp per side on absolute notional turnover, with retained 28 bp and 56 bp round-trip-equivalent stress using identical turnover accounting.

For non-24/7 assets, preserve the same causal concept using the exchange trading-session calendar: signal through completed session `t`, position for the next completed trading session. Do not fabricate weekend/holiday sessions. Asset-specific unavoidable roll/spread/slippage costs must be added under a separately source-frozen execution addendum without changing the V1 signal.

## Validation stack and sequencing
Each lane must freeze source provenance, normalized data bytes/hash, mapping/session semantics, and exact runner bytes/hash BEFORE its first performance read. Failure of this order downgrades that lane to diagnostic-only evidence.

### V1-V1 — genuinely independent-time BTC
Priority lane. Use BTC history chronologically disjoint from the consumed Binance USD-M development window beginning 2019-09-08, if a source with adequate >=60-day warm-up exists and has not been consumed for V1 outcomes. Spot/perpetual basis differences must be reported, not hidden. This lane answers temporal generalization.

### V1-V2 — same-calendar cross-venue BTC
Use an unconsumed alternative BTC venue/instrument with overlapping dates only after its source/data/runner freeze. Same-calendar cross-venue evidence is explicitly NOT independent-time evidence. This lane answers venue/data-source stability.

### V1-V3 — unchanged cross-asset transport
After V1-V1/V2 evidence is recorded, transport the exact 20/60/1.25 state rule without retuning. Preferred sequence: exact COMEX Gold futures when durable frozen outright data is ready; then broad equity-index futures/ETF proxy under explicitly labeled instrument lineage; later other liquid assets. External-market results cannot feed back into BTC V1 thresholds or horizons.

## Mandatory diagnostics
For V1 and the same-market always-long benchmark retain:
- coverage and warm-up boundaries;
- baseline and 28/56bp stress terminal net return;
- annualized Sharpe;
- MaxDD and worst calendar year/era;
- turnover and fraction of time invested/flat;
- positive/negative calendar-year and preregistered era breadth;
- return and drawdown during V1-flat volatility-expansion states versus invested states;
- concentration: best-year removal and leave-one-era-out where sample size permits;
- tail diagnostics: worst daily/session return and lower-tail quantiles;
- benchmark-relative incremental return, drawdown reduction, and downside capture;
- deterministic rerun identity and exact artifact hashes.

A high terminal return alone cannot promote V1. Because V1 is long-or-flat, benchmark-relative evidence is mandatory: a useful result should show economically meaningful drawdown/tail reduction or risk-adjusted improvement without depending on one era and without being erased by plausible costs.

## Decision labels
Possible labels are retained regardless of outcome:
1. `REJECTED_VALIDATION` — external evidence materially adverse/fragile.
2. `RISK_CONTROL_ONLY_SUPPORTIVE` — improves drawdown/tails/risk-adjusted behavior but does not justify standalone Alpha language.
3. `SUPPORTIVE_VOLATILITY_STATE_EFFECT` — reproducible benchmark-relative effect across appropriate independent-time/venue evidence, still not automatically portfolio-ready.
4. `CROSS_ASSET_GENERALIZABLE_SUPPORT` — unchanged transport additionally survives materially different asset classes.

None of these labels alone sets `Validated Alpha = YES`; final status remains subject to the project-wide historical OOS/walk-forward/cross-market governance stack.

## Anti-contamination rules
- No threshold neighborhood search on reserved validation data.
- No 20/60 horizon search on reserved validation data.
- No adding direction, trend, funding, calendar, stop, target, leverage, or sizing rules after seeing validation outcomes.
- No selective deletion of bad years/eras/venues/assets.
- No ensemble with `VM_TSMOM20`, `TSMOM_120`, Candidate A, or any later Alpha until standalone evidence is recorded.
- Every null/adverse lane is retained.
- If an engineering defect is discovered, repair mechanics only, document it, and rerun under a new hash; do not change the economic rule.

## Immediate authorized next actions
1. Acquire and freeze an unconsumed independent-time BTC daily source for V1-V1 where feasible, with >=60-day pre-evaluation warm-up.
2. In parallel continue first-party Kraken V2b acquisition for the separate Cycle-1 trend validation lineage; do not reuse its outcomes to tune V1.
3. Keep GC exact transport frozen until durable COMEX outright payload is available; equity-index data remains SOURCE-ONLY until its transport protocol is frozen.
4. Do not ensemble V1 with trend representatives yet.

# Broad Discovery Cycle-2 Preregistration

Date: 2026-09-18
Status: FROZEN BEFORE CYCLE-2 PERFORMANCE READ
Development substrate: already-consumed Binance BTCUSDT USD-M historical data only. Reserved holdouts, V2/V3 validation sources, GC transport, and SOURCE-ONLY equity-index datasets are excluded.

## Objective
Search structurally independent mechanisms rather than variants of Cycle-1 trend. Cycle-1 trend survivors remain separate. Cycle-2 is not allowed to ensemble with them during discovery.

## Priority families and causal rationale
A. Funding/carry state: persistent funding can proxy crowded directional demand / leverage cost. Test simple funding-sign and extreme-state mechanisms only if point-in-time funding history is available without leakage.
B. Futures basis/premium state: mark/index or premium divergence may proxy leverage imbalance and mean reversion / continuation conditional states. Use only point-in-time series available before execution.
C. Volatility-regime mechanism independent of trend direction: realized-volatility state transitions / compression-expansion. Directional exposure, if any, must be defined ex ante and not borrow the Cycle-1 TSMOM sign.
D. Calendar/seasonality benchmark: low-DOF UTC day-of-week/month-state rules as a falsification/control family, not data-mined calendar grids.

## Batch discipline
Target 6–12 total candidates across >=3 structurally distinct families, subject to exact data availability. Freeze exact formulas, horizons, execution clock, costs and candidate count in an implementation addendum BEFORE the first outcome read. Retain every candidate. No post-outcome candidate additions to this cycle. If a family lacks causal historical data, record DATA_UNAVAILABLE rather than proxying it after outcomes.

## Common evaluation
Use already-consumed BTC development calendar only. Next-observable execution; no same-bar lookahead. Baseline 7bp/side where directional turnover occurs; preregistered 28/56bp round-trip stress for comparable directional strategies. For continuous notional strategies charge turnover. Report terminal net return, annualized Sharpe, MaxDD, turnover, chronological era/block sign breadth, worst block, concentration, and cost stress where applicable. Family-aware selection comes before aggregate Sharpe/return.

## Multiple testing / researcher DOF
All tested members retained. One representative maximum per family can advance from this cycle. Promotion priority: era/regime sign breadth, worst-era behavior, drawdown/tails, cost tolerance, parameter-neighborhood support where preregistered, simplicity and economic rationale; aggregate return/Sharpe are secondary. No max-Sharpe winner selection across the whole grid. No threshold search after outcomes. No ensemble in Cycle-2.

## Validation
Any survivor requires a separately frozen historical validation plan before touching any still-unread validation source. Cross-venue same-calendar evidence is not independent-time evidence. Validated Alpha remains NO.

## Exact next implementation task
Audit connected Binance historical availability for funding rate and premium/mark/index series over the consumed development calendar. Freeze exact Cycle-2 candidate formulas only after the causal data fields/coverage are known, without computing strategy performance. In parallel continue V2 source recovery/audit and SOURCE-ONLY equity-index engineering.

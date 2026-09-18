# Broad Discovery Cycle-2 — Implementation Freeze

Frozen 2026-09-18 before any Cycle-2 performance read.

## Governance
Development substrate only: already-consumed Binance BTCUSDT USD-M calendar. No reserved holdout, Kraken V2b, GC, or equity-index transport data may be used for selection/tuning. All outcomes retained. No post-outcome grid expansion. One representative maximum per family may be promoted. `Validated Alpha = NO` unless later governance formally changes it.

Execution for directional candidates: signal from information available by UTC day close t; position applies to next UTC daily open-to-open return (t+1). Baseline transaction friction 7 bp per side on absolute notional turnover; stress reads 28 bp and 56 bp round-trip-equivalent using the same turnover accounting. No lookahead/interpolation.

## Source-coverage audit known before outcomes
- BTCUSDT USD-M funding history is queryable from 2019-09-10 onward at native funding timestamps.
- BTCUSDT USD-M premium-index daily klines are queryable but begin later (observed first available daily bar 2019-12-24 in launch-era probe). Premium-family evaluation therefore uses its own later common-coverage window and may not be directly ranked on terminal return against full-window families without coverage-aware diagnostics.

## Frozen candidate grid

### Family F — Funding/carry state
Native funding payments are summed by UTC calendar day; no missing payment is fabricated.
- F1 FUNDING_CONTRA_7D: rolling 7-calendar-day sum of funding through day t. Position for t+1 = -sign(sum), with zero if exactly zero.
- F2 FUNDING_CONTRA_30D: same using rolling 30-calendar-day sum.
- F3 FUNDING_EXTREME_30D: expanding-history z-score of the 30-day funding sum, requiring >=180 calendar days of prior observations; position = -sign(z) only when |z| >= 1.0, else 0. Expanding mean/std use only data through t.
Economic interpretation: crowded positive funding implies expensive longs / short carry; negative funding implies expensive shorts / long carry. These are tested as state signals, not assumed alpha.

### Family P — Futures premium/basis state
Daily premium-index close is used as the observable state; no price-derived substitute.
- P1 PREMIUM_CONTRA_LEVEL: position t+1 = -sign(premium_close_t).
- P2 PREMIUM_CONTRA_7D: position t+1 = -sign(7-day simple mean premium close through t).
- P3 PREMIUM_EXTREME_EXPANDING: expanding z-score of premium close with >=180 prior daily observations; position = -sign(z) if |z| >= 1.0 else 0.
Economic interpretation: persistent positive premium can encode crowded long demand/carry cost; negative premium the converse. Separate from realized-price trend ancestry.

### Family V — Volatility-regime transition, direction-independent
Use daily close-to-close log returns from consumed BTC development OHLCV. RV20 = sqrt(365) * population std of last 20 daily log returns; RV60 analogously 60 days. No price-direction sign enters the signal.
- V1 VOL_EXPANSION_FLAT: position = 0 when RV20/RV60 > 1.25, otherwise +1. This is a risk-state control, not presumed standalone alpha.
- V2 VOL_COMPRESSION_LONG: position = +1 when RV20/RV60 < 0.80, otherwise 0.
- V3 VOL_STATE_SWITCH: +1 when ratio < 0.80; 0 when 0.80 <= ratio <= 1.25; -1 when ratio > 1.25. This tests whether volatility expansion itself carries directional information; expected to be fragile and retained even if adverse.

### Family C — Low-DOF calendar control
- C1 WEEKEND_FLAT: long except position 0 for next-day Saturday/Sunday UTC returns.
- C2 WEEKEND_ONLY: long only for next-day Saturday/Sunday UTC returns.
- C3 MONTH_END_3D: long only when the next UTC date is one of the final 3 calendar days of its month; otherwise 0.
These are deliberately low-DOF controls and must not be mined across weekday/month grids after outcomes.

## Required diagnostics
For every candidate: baseline net terminal return, annualized Sharpe, MaxDD, turnover, exposure, calendar-year/era sign breadth, worst year/era, 28/56 bp cost stress, and concentration diagnostics. Coverage start/end must be explicit. Family triage prioritizes sign breadth, worst-era behavior, drawdown, cost tolerance, simplicity and coverage before terminal return/Sharpe.

## Promotion rule
At most one representative per family may leave Cycle-2. A family can be rejected wholesale. No ensemble construction in Cycle-2. Survivors require a separately frozen validation plan before any reserved or transport performance is read.

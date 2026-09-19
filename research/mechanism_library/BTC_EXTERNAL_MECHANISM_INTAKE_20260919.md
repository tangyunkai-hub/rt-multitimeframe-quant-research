# BTC External Mechanism Intake — 2026-09-19

Status: HYPOTHESIS / MECHANISM LIBRARY ONLY. No strategy performance read. No reserved holdout touched. This memo does not authorize parameter selection, ensemble construction, or promotion.

## Purpose
BTC-first external-intelligence intake after Cycle-2 V1 adverse independent-time adjudication. Sources are mechanism generators, not evidence that an implementable Alpha exists in our data.

## Intake A — Crypto time-series momentum / attention
Source: Liu & Tsyvinski, “Risks and Returns of Cryptocurrency,” NBER w24877 (2018), later Review of Financial Studies 2021.
Mechanism claim: cryptocurrency returns exhibit strong time-series momentum; investor-attention proxies forecast returns; crypto risk/return structure differs from traditional stocks/currencies/precious metals.
Research implication: supports keeping trend/momentum as a first-class BTC family, but does not validate our frozen TSMOM_120 or VM_TSMOM20 implementation. Attention is a structurally separate future family if timestamp-clean historical attention data can be sourced.
DOF/fitting risk: medium; source investigates multiple predictors. Any implementation must be preregistered on consumed development data before outcome read.
IP/license: paper mechanism only; no code copied.

## Intake B — Crypto cross-sectional momentum / factor structure
Source: Liu, Tsyvinski & Wu, “Common Risk Factors in Cryptocurrency,” NBER w25882 (2019), Journal of Finance 2022.
Mechanism claim: crypto market, size, and momentum factors capture cross-sectional expected crypto returns; several price/market long-short factors are subsumed by a three-factor structure.
Research implication: high-priority later BTC-ecosystem / multi-crypto cross-sectional family, but not a single-BTC standalone signal. Requires a liquid multi-asset universe, point-in-time survivorship handling, delisting treatment, and realistic short/borrow/perpetual execution.
DOF/fitting risk: medium-high due broad factor menu and universe construction.
IP/license: paper mechanism only; no code copied.

## Intake C — Crypto-specific momentum behavior
Source: Kogan, Makarov, Niessner & Schoar, “Are Cryptos Different? Evidence from Retail Trading,” NBER w31317 (2023), Journal of Financial Economics 2024.
Mechanism claim: the same retail traders are contrarian in stocks/gold but momentum-like in crypto; authors argue crypto price changes may alter perceived adoption probabilities and reinforce trends.
Research implication: economic rationale for crypto trend persistence and for explicitly testing regime/horizon dependence rather than assuming stock/gold behavior transports unchanged.
DOF/fitting risk: low as a rationale source; it is not a trading-rule paper.
IP/license: mechanism/rationale only.

## Intake D — Periodic volatility/liquidity structure
Source: “Periodicity in Cryptocurrency Volatility and Liquidity,” Journal of Financial Econometrics 22(1), 2024 (published online 2022).
Mechanism claim: BTC/ETH volatility and volume show systematic day-of-week, hour-of-day, and within-hour periodicity across Coinbase Pro, Binance and Uniswap V2; patterns strengthened over time and may relate to algorithmic trading and futures funding times.
Research implication: do NOT resurrect the rejected daily calendar controls. Instead open a future intraday execution/state hypothesis family only when clean intraday data and cost model are available: periodic liquidity/volatility state may change execution quality or conditional signal efficacy without itself being directional Alpha.
DOF/fitting risk: high if many clock buckets are searched; any test needs a very low-DOF preregistered clock partition and multiple-testing control.
IP/license: paper mechanism only.

## Intake E — Bitcoin jump/order-flow microstructure
Source: “High-Frequency Jump Analysis of the Bitcoin Market,” Journal of Financial Econometrics 18(2), 2020.
Mechanism claim: jumps cluster; order-flow imbalance, aggressive trading and wider bid-ask spread predict jumps in the historical Mt. Gox sample; jumps affect activity and illiquidity.
Research implication: candidate microstructure family for later intraday/tick research, not appropriate for current daily BTC Alpha Map release gate unless modern multi-venue order-book/trade data and latency-realistic execution are available.
DOF/fitting risk: high transport risk because source market structure is old and venue-specific.
IP/license: paper mechanism only.

## Intake F — Recent adaptive trend paper (lower evidence tier)
Source: Bui & Nguyen, “Systematic Trend-Following with Adaptive Portfolio Construction: Enhancing Risk-Adjusted Alpha in Cryptocurrency Markets,” arXiv:2602.11708 (2026).
Mechanism claim: 6-hour trend, adaptive asset selection, trailing stops and asymmetric long/short portfolio construction reported across 150+ crypto pairs.
Research implication: hypothesis source for later multi-crypto/horizon work only. Do not import reported parameter choices or reported Sharpe as evidence. High researcher-DOF / recent-preprint risk; treat below peer-reviewed/NBER sources.
IP/license: no code copied; implementation would require independent formulation and license/FTO review if code is later considered.

## Prioritization for BTC-first roadmap
1. Preserve trend/momentum as current top validation priority (Kraken V2b) because independent literature supplies economic/empirical rationale and our own frozen discovery already has survivors.
2. Next new daily/swing development cycle should favor structurally distinct, low-DOF mechanisms rather than more trend parameter variants. Attention is promising only if timestamp-clean data can be obtained without leakage.
3. Cross-sectional crypto momentum belongs after first releasable single-BTC Alpha Map v1 or as a separate multi-crypto extension, not as a blocker to BTC v1.
4. Intraday periodic liquidity and order-flow/jump mechanisms belong to a later intraday cell with explicit execution/latency economics; they must not be inferred from daily backtests.
5. No source in this intake changes `Validated Alpha = NO` and none authorizes tuning on reserved data.

## Governance classification
`EXTERNAL_MECHANISM_INTAKE_COMPLETE__HYPOTHESIS_ONLY__NO_PERFORMANCE__NO_HOLDOUT_TOUCH__BTC_FIRST_PRIORITIES_REFINED`

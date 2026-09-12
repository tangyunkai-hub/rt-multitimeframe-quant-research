# Cross-Exchange Execution Robustness — Coinbase 2017–2022

**Classification:** `CROSS_EXCHANGE_EXECUTION_ROBUSTNESS_NOT_PROSPECTIVE`  
**Protocol frozen before Coinbase performance was read:** `research/cross_exchange_execution_prereg_2026-09-12.md`  
**Data workflow:** GitHub Actions run `34699255006` — `success`  
**Data artifact:** `rt-cross-exchange-coinbase-2017-2022`, artifact id `10299497700`, digest `sha256:8fc7692bd5497a154be6867f79388fde9943ecb7d70ed8b8607b9c3f61403d42`  
**Frozen evaluator commit before result inspection:** `df2f8bf6e41c2656a1da89c2f9e154130c8d9a24`

## Purpose

This test holds the frozen implementation-compatibility-v3 Candidate A/B state timelines fixed and changes only the execution/PnL venue from Binance Spot to Coinbase Exchange. Coinbase prices never feed signal or state generation. The test asks whether the previously recorded BTC/ETH mechanism directions are venue-sensitive.

## Data integrity gate

Performance was not read until the Coinbase data-only gate passed. No missing candles were synthesized; old exposure carries across venue gaps and a new state waits for the next observed Coinbase open.

| Product | Rows | First bar | Last bar | Duplicate timestamps | OHLC failures | Nonpositive price rows | Gap events | Missing 15m intervals | Normalized SHA-256 |
|---|---:|---|---|---:|---:|---:|---:|---:|---|
| BTC-USD | 188,260 | 2017-08-17 00:00:00+00:00 | 2022-12-31 23:45:00+00:00 | 0 | 0 | 0 | 30 | 188 | `bd77a2d1b37890d0a9fc7f260cfb139ea1d0671f61696ee3176c5e0b087439e5` |
| ETH-USD | 188,348 | 2017-08-17 00:00:00+00:00 | 2022-12-31 23:45:00+00:00 | 0 | 0 | 0 | 25 | 100 | `f879ed7297e2217dc1abc4c9c32c5321e84d8755cced9fccce1dd1b2176fe73a` |

## Frozen primary results — 7bp one-way cost

| Asset | Coinbase A return | Coinbase B return | Coinbase paired Δ log B−A | Bear epochs favoring B | Coinbase label | Locked Binance label | Venue verdict |
|---|---:|---:|---:|---:|---|---|---|
| BTC | +971.98% | +805.59% | -0.168675 | 1/3 | `ADVERSE_EXTERNAL_MECHANISM_EVIDENCE` | `ADVERSE_EXTERNAL_MECHANISM_EVIDENCE` | `VENUE_CONSISTENT` |
| ETH | -4.73% | +11.01% | +0.152917 | 3/4 | `EXTERNAL_MECHANISM_SUPPORT` | `EXTERNAL_MECHANISM_SUPPORT` | `VENUE_CONSISTENT` |

Both assets are `VENUE_CONSISTENT`: BTC remains adverse to Candidate B, while ETH remains supportive. The earlier BTC/ETH heterogeneity therefore does not disappear when execution/PnL is moved from Binance to Coinbase.

## Fixed cost stress

| Asset | Total one-way cost | Paired Δ log B−A | Label | Venue verdict |
|---|---:|---:|---|---|
| BTC | 7bp | -0.168675 | `ADVERSE_EXTERNAL_MECHANISM_EVIDENCE` | `VENUE_CONSISTENT` |
| BTC | 9bp | -0.158271 | `ADVERSE_EXTERNAL_MECHANISM_EVIDENCE` | `VENUE_CONSISTENT` |
| BTC | 12bp | -0.142661 | `ADVERSE_EXTERNAL_MECHANISM_EVIDENCE` | `VENUE_CONSISTENT` |
| ETH | 7bp | +0.152917 | `EXTERNAL_MECHANISM_SUPPORT` | `VENUE_CONSISTENT` |
| ETH | 9bp | +0.160923 | `EXTERNAL_MECHANISM_SUPPORT` | `VENUE_CONSISTENT` |
| ETH | 12bp | +0.172934 | `EXTERNAL_MECHANISM_SUPPORT` | `VENUE_CONSISTENT` |

The frozen 7/9/12bp one-way cost scenarios do not flip either asset’s directional mechanism label.

## Descriptive Binance–Coinbase agreement

These diagnostics were computed after the frozen venue verdict and are descriptive only; they are not a new pass/fail gate.

| Asset | Segment count Bn/Cb | Segment Δ correlation | Segment sign concordance | Epoch count Bn/Cb | Epoch Δ correlation | Epoch sign concordance |
|---|---:|---:|---:|---:|---:|---:|
| BTC | 26/26 | 0.999816 | 100% | 3/3 | 0.999980 | 100% |
| ETH | 20/20 | 0.999925 | 100% | 4/4 | 0.999810 | 100% |

All segment and epoch signs match across venues in both assets; the paired-delta correlations are approximately 0.9998 or higher. This strongly suggests that the external historical mechanism split is not an artifact of one execution venue.

## Invariants

For BTC and ETH, every frozen state/execution invariant passed with zero failures: Major direction identical between A/B, Long occupancy identical, Candidate B never adds Short exposure, and every A/B executed divergence is exactly Candidate A short versus Candidate B flat.

## Research-status impact

- This strengthens **execution-venue robustness** of the historical finding.
- It does **not** make the 2017–2022 evidence prospective.
- It does **not** validate Candidate B: BTC remains adverse while ETH remains supportive.
- It does **not** erase the immutable v0.22 holdout failure.
- v0.24 remains `INSUFFICIENT_FORWARD_EVIDENCE`.
- Validated Alpha is still **not established**.
- `SMALL_CAPITAL_LIVE_ELIGIBLE` remains **false**.

## Anti-overfit lock

No signal/state semantics, threshold, sizing rule, cost protocol, adapter rule, or Candidate B permission may be changed based on these Coinbase results.

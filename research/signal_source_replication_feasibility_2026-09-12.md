# Independent Signal-Source Replication — Feasibility Gate

**Date:** 2026-09-12  
**Status:** `BLOCKED_NO_SURVEYED_SINGLE_PROVIDER_EXACT_NATIVE_TIMEFRAME_COVERAGE`  
**Research impact:** no strategy result was read and no strategy rule was changed.

## Question

Can the frozen implementation-compatibility-v3 signal/state engine be recreated on one independent public market-data provider using the same required native bar clocks, without substituting lower-timeframe resampling for missing native intervals?

This is a different question from the completed Coinbase cross-exchange test. Coinbase changed execution/PnL only while keeping the frozen state trajectories fixed. A true signal-source replication would rebuild the state trajectories from independent market bars.

## Required native clock set

The external-validation adapter uses the project’s frozen native timeframe set, including the critical higher clocks `2h`, `8h`, `12h`, `3d`, and `1w` in addition to lower clocks. Previous adapter work demonstrated that apparently reasonable lower-timeframe reconstruction can change authority-critical state/action semantics. Therefore a missing native clock is not silently synthesized for this gate.

## Public API coverage survey

This survey checks interval availability only. It does not inspect strategy performance.

| Provider | Relevant documented native intervals | Gap versus frozen set |
|---|---|---|
| KuCoin Spot | 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 1w | no documented 3d |
| OKX Spot history candles | 15m, 30m, 1H, 2H, 4H, 6H/12H, 1D/2D/3D/1W (including UTC variants for higher bars) | no documented 8h |
| Bybit Spot | 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d, 1w | no documented 8h or 3d |
| Gate Spot | 15m, 30m, 1h, 4h, 8h, 1d, 7d | no documented 2h, 12h, or 3d |
| Bitget current market API | 15m, 30m, 1H, 4H, 6H, 12H, 1D | no complete coverage of 2h, 8h, 3d, 1w in the current endpoint |

Official references checked:

- KuCoin Klines: https://www.kucoin.com/docs-new/3470071w0
- OKX API v5 market history candles: https://www.okx.com/docs-v5/en/
- Bybit v5 Get Kline: https://bybit-exchange.github.io/docs/v5/market/kline
- Gate API v4 Spot candlesticks: https://www.gate.com/docs/developers/apiv4/en/spot/
- Bitget Market Data: https://www.bitget.com/docs/catalog/market/market-data

## Gate decision

No surveyed single provider exposes the full exact native timeframe set required for a clean one-provider recreation. Therefore:

1. **Do not** substitute arbitrary lower-timeframe resampling and label it independent native-source replication.
2. **Do not** read source-replication performance from a partially compatible adapter.
3. The single-provider independent signal-source gate remains `BLOCKED_NO_SURVEYED_SINGLE_PROVIDER_EXACT_NATIVE_TIMEFRAME_COVERAGE`.
4. This is an availability limitation, not a strategy failure and not evidence for or against Alpha.

## Possible future route: preregistered multi-provider mosaic

A technically possible follow-up would use a predeclared provider priority per native timeframe—for example one provider for 8h and another for 3d—while keeping all signal formulas and thresholds frozen. That would answer a different question: robustness to a deliberately multi-provider state-input mosaic.

Such a test is **not authorized by this feasibility note**. Before any mosaic result is read it would require:

- an explicit source/timeframe map;
- bar-boundary and completed-bar availability rules;
- listing/warm-up eligibility rules;
- semantic regression on a consumed modern window;
- a new preregistration and immutable freeze commit;
- zero strategy tuning from the result.

## Current project consequence

The completed evidence remains unchanged:

- v0.22 holdout failure is immutable;
- BTC external history is adverse to Candidate B;
- ETH external history is supportive;
- the BTC/ETH split is execution-venue robust on Coinbase;
- Candidate B remains `FROZEN_HYPOTHESIS_NOT_VALIDATED`;
- v0.24 remains `INSUFFICIENT_FORWARD_EVIDENCE`;
- validated Alpha is not established;
- small-capital live eligibility remains false.

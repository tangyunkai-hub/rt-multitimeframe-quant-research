# RT Multi-Timeframe Quant Research
## A Public Technical Summary of an Auditable Prospective Research System

**Status:** Research-only / not deployment-ready

## Abstract

This project converts a discretionary multi-timeframe Bitcoin framework into a versioned quantitative research system. The public release focuses on methodology rather than proprietary signal construction. It demonstrates source-authority controls, completed-bar causality, event-driven campaign states, asymmetric permissions, robustness diagnostics, frozen holdout evaluation, failure attribution, prospective A/B design, causal execution, deterministic paper simulation, pre-registered external historical validation, and cross-exchange execution robustness.

Retrospective development produced an aggregate return near +257.9% with Sharpe near 2.01, but later diagnostics showed substantial nonstationarity and concentration. The frozen performance holdout then failed: approximately -21.61% total return, -1.15 Sharpe, and -38.02% maximum drawdown. The failure was retained as immutable evidence.

Post-holdout work did not optimize the same period. Instead, attribution isolated one automatic same-direction Short re-entry permission whose source authority was weaker than its engineering implementation. Candidate B removes that automatic core-restoration permission only. Candidate B is a post-holdout hypothesis, not a validated improvement, and can be confirmed only on genuinely new data.

A separately frozen 2017–2022 external historical program was then executed without changing Candidate B. BTC produced adverse evidence for Candidate B, while ETH produced supportive evidence. The cross-asset result is heterogeneous rather than uniformly confirmatory. Repeating the PnL/execution test on Coinbase while holding the signal/state trajectories fixed reproduced the same BTC-adverse / ETH-supportive split, making the finding execution-venue robust but still retrospective.

## Research governance

The project distinguishes development, robustness, frozen holdout, external historical validation, and prospective confirmation. Once a dataset is consumed, it cannot later become confirmation data for a candidate created after that consumption boundary. Failed and contradictory results remain part of the permanent record.

## Causality

All strategy inputs are normalized events available only after their source bars close. Research returns shift exposure causally, and execution fills may occur no earlier than the next observed native bar open. Across gaps, old exposure remains in force until the next observed fill. This prevents same-bar hindsight profit attribution.

## State authority

A confirmed directional regime persists until an opposite confirmed event. Local contrary or provisional evidence may degrade the current regime to an at-risk state, but does not automatically reverse direction. Risk roles, core direction, exits, and re-entry watches remain separate state dimensions.

## Retrospective evidence

The attractive aggregate historical result was not treated as stationary alpha. Later-period deterioration, sparse Long campaigns, concentrated campaign contribution, fragile Short independence, and parameter sensitivity were recorded before the holdout.

## Holdout failure

The frozen holdout failed materially. The project therefore remained not deployment-ready. Cost stress did not explain the failure away, and campaign/event audits found no engine-authority violation sufficient to dismiss the result as an implementation bug.

## Failure attribution

Short exposure contributed the majority of absolute holdout log-loss through repeated local whipsaw, while Long exposure included a material multi-month drawdown. Several nominal Short trades occurred inside the same prolonged higher-level regime, illustrating why raw trade count is not an independent sample size.

## Candidate B

Candidate B changes one permission only: after a local Short structural invalidation and hard exit, a subsequent same-level re-entry signal inside the same continuous bearish regime remains diagnostic/probe-only rather than automatically restoring a core Short position.

The public repository abstracts the proprietary event definitions that generate these signals.

## Prospective evaluation

Candidate A/B evidence is measured on paired divergence segments—the intervals where the one changed permission produces different states. Results are also aggregated by continuous bearish regime episode as the higher-level replication unit. Formal prospective support is not eligible until a preregistered minimum amount of genuinely new forward evidence accumulates.

The frozen v0.24 floor is at least 180 forward days, 3 independent Major Bear divergence epochs, and 6 divergence segments. Until all are met, the status remains `INSUFFICIENT_FORWARD_EVIDENCE` regardless of historical performance.

## External historical validation

Before reading 2017–2022 Candidate A/B performance, the project froze an external evaluation protocol and a compatibility adapter that exactly reproduced authority-critical modern states and actions. The primary comparison uses core exposure, 14bp round-trip cost, next-observed-open execution, and continuous bearish regime episodes as the independent mechanism unit.

On BTC, 26 paired divergence segments occurred across 3 independent bearish divergence epochs. Candidate B had negative paired delta log versus Candidate A, only 1 of 3 epochs favored B, and leave-one-epoch-out remained unstable/negative. The frozen protocol therefore labels BTC `ADVERSE_EXTERNAL_MECHANISM_EVIDENCE`.

On ETH, the exact same frozen mechanism produced 20 divergence segments across 4 independent bearish divergence epochs. Candidate B had positive paired delta log, 3 of 4 epochs favored B, and all leave-one-epoch-out totals remained positive. The frozen protocol therefore labels ETH `EXTERNAL_MECHANISM_SUPPORT`.

The two assets therefore do not provide uniform cross-asset replication. Fixed 0/2/5bp one-way slippage stress did not change either asset's qualitative label. Independent-epoch counts remain small, so no conventional statistical-significance claim is made.

These results are explicitly `EXTERNAL_HISTORICAL_VALIDATION_NOT_PROSPECTIVE`: they may strengthen or weaken hypotheses but cannot validate Candidate B or erase the failed v0.22 holdout.

## Cross-exchange execution robustness

A separate Coinbase execution/PnL protocol was frozen before reading Coinbase strategy performance. The frozen Candidate A/B state trajectories were held constant and only the execution venue changed from Binance Spot to Coinbase Exchange 15-minute candles. Coinbase prices did not enter signal or state generation, and missing exchange candles were not synthesized.

The data-only gate passed for both BTC-USD and ETH-USD. Under the frozen 14bp round-trip baseline, BTC remained adverse to Candidate B and ETH remained supportive. Segment- and Bear-epoch-level signs matched across Binance and Coinbase for both assets, with paired-delta correlations near one. The same qualitative labels also survived the frozen 7/9/12bp one-way total-cost ladder.

This is classified `CROSS_EXCHANGE_EXECUTION_ROBUSTNESS_NOT_PROSPECTIVE`. It reduces the plausibility that the BTC/ETH split is a Binance-specific PnL artifact; it does not resolve the cross-asset heterogeneity or create prospective evidence.

## Execution and paper simulation

A separate execution layer applies next-open fills, fees, and fixed adverse-slippage scenarios without altering strategy permission.

The brokerless v0.28 paper-shadow layer is now engineering-hardened but not live. It uses an append-only JSONL audit journal with SHA-256 record chaining, canonical bar hashes, state-before/state-after hashes, deterministic full-journal restart recovery, idempotent identical-bar replay, hard failure when data change at an already processed timestamp, stale-state protection, and tamper detection. These are engineering guarantees only; sustained paper-market evidence still requires genuinely new data.

## Reproducibility

Run manifests hash exact input bytes and can preserve stable relative paths. Duplicate manifest keys fail closed rather than silently overwriting one another. Verification checks the manifest self-hash and current input bytes, so altered data or altered metadata invalidate provenance. The public test suite runs across Python 3.10, 3.11, and 3.12.

## Current conclusion

The project demonstrates research discipline and engineering architecture, not validated trading alpha. Historical evidence is materially heterogeneous: BTC argues against the post-holdout Short-suppression mechanism while ETH argues for it, and that split persists across Binance and Coinbase execution. The central unresolved requirement remains independent prospective market evidence. Candidate B is still frozen but unvalidated, v0.24 remains insufficient in forward evidence, v0.25/v0.26 remain unvalidated, and the system is not eligible for small-capital live deployment.

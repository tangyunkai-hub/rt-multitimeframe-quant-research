# RT Multi-Timeframe Quant Research
## A Public Technical Summary of an Auditable Prospective Research System

**Status:** Research-only / not deployment-ready

## Abstract

This project converts a discretionary multi-timeframe Bitcoin framework into a versioned quantitative research system. The public release focuses on methodology rather than proprietary signal construction. It demonstrates source-authority controls, completed-bar causality, event-driven campaign states, asymmetric permissions, robustness diagnostics, frozen holdout evaluation, failure attribution, prospective A/B design, causal execution, deterministic paper simulation, and pre-registered external historical validation.

Retrospective development produced an aggregate return near +257.9% with Sharpe near 2.01, but later diagnostics showed substantial nonstationarity and concentration. The frozen performance holdout then failed: approximately -21.61% total return, -1.15 Sharpe, and -38.02% maximum drawdown. The failure was retained as immutable evidence.

Post-holdout work did not optimize the same period. Instead, attribution isolated one automatic same-direction Short re-entry permission whose source authority was weaker than its engineering implementation. Candidate B removes that automatic core-restoration permission only. Candidate B is a post-holdout hypothesis, not a validated improvement, and can be confirmed only on genuinely new data.

A separately frozen 2017–2022 external historical program was then executed without changing Candidate B. BTC produced adverse evidence for Candidate B, while ETH produced supportive evidence. The cross-asset result is therefore heterogeneous rather than uniformly confirmatory. This older history remains retrospective external evidence and does not count toward prospective confirmation.

## Research governance

The project distinguishes development, robustness, frozen holdout, external historical validation, and prospective confirmation. Once a dataset is consumed, it cannot later become confirmation data for a candidate created after that consumption boundary.

## Causality

All strategy inputs are normalized events available only after their source bars close. Research returns shift exposure causally, and execution fills may occur no earlier than the next observed native bar open. Across gaps, old exposure remains in force until the next observed fill. This prevents same-bar hindsight profit attribution.

## State authority

A confirmed directional regime persists until an opposite confirmed event. Local contrary evidence may degrade the current regime to an at-risk state, but does not automatically reverse direction. Risk roles, core direction, exits, and re-entry watches remain separate state dimensions.

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

## External historical validation

Before reading 2017–2022 Candidate A/B performance, the project froze an external evaluation protocol and a compatibility adapter that exactly reproduced authority-critical modern states and actions. The primary comparison uses core exposure, 14bp round-trip cost, next-observed-open execution, and continuous bearish regime episodes as the independent mechanism unit.

On BTC, 26 paired divergence segments occurred across 3 independent bearish divergence epochs. Candidate B had negative paired delta log versus Candidate A, only 1 of 3 epochs favored B, and leave-one-epoch-out remained unstable/negative. The frozen protocol therefore labels BTC `ADVERSE_EXTERNAL_MECHANISM_EVIDENCE`.

On ETH, the exact same frozen mechanism produced 20 divergence segments across 4 independent bearish divergence epochs. Candidate B had positive paired delta log, 3 of 4 epochs favored B, and all leave-one-epoch-out totals remained positive. The frozen protocol therefore labels ETH `EXTERNAL_MECHANISM_SUPPORT`.

The two assets therefore do not provide uniform cross-asset replication. Fixed 0/2/5bp one-way slippage stress did not change either asset's qualitative label. Independent-epoch counts remain small, so no conventional statistical-significance claim is made.

These results are explicitly `EXTERNAL_HISTORICAL_VALIDATION_NOT_PROSPECTIVE`: they may strengthen or weaken hypotheses but cannot validate Candidate B or erase the failed v0.22 holdout.

## Execution and paper simulation

A separate execution layer applies next-open fills, fees, and fixed adverse-slippage scenarios without altering strategy permission. A deterministic paper-shadow engine uses data hashes, state hashes, idempotent replay, restart recovery, and hard failure on silent historical corrections.

## Current conclusion

The project demonstrates research discipline and engineering architecture, not validated trading alpha. Historical evidence is materially heterogeneous: BTC argues against the post-holdout Short-suppression mechanism while ETH argues for it. The central unresolved requirement remains independent prospective market evidence. Candidate B is still frozen but unvalidated, v0.24 remains insufficient in forward evidence, and the system is not eligible for small-capital live deployment.

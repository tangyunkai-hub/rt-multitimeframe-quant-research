# RT Multi-Timeframe Quant Research
## A Public Technical Summary of an Auditable Prospective Research System

**Status:** Research-only / not deployment-ready

## Abstract

This project converts a discretionary multi-timeframe Bitcoin framework into a versioned quantitative research system. The public release focuses on methodology rather than proprietary signal construction. It demonstrates source-authority controls, completed-bar causality, event-driven campaign states, asymmetric permissions, robustness diagnostics, frozen holdout evaluation, failure attribution, prospective A/B design, causal execution, and deterministic paper simulation.

Retrospective development produced an aggregate return near +257.9% with Sharpe near 2.01, but later diagnostics showed substantial nonstationarity and concentration. The frozen performance holdout then failed: approximately -21.61% total return, -1.15 Sharpe, and -38.02% maximum drawdown. The failure was retained as immutable evidence.

Post-holdout work did not optimize the same period. Instead, attribution isolated one automatic same-direction Short re-entry permission whose source authority was weaker than its engineering implementation. Candidate B removes that automatic core-restoration permission only. Candidate B is a post-holdout hypothesis, not a validated improvement, and can be confirmed only on genuinely new data.

## Research governance

The project distinguishes four evidence pools: development, robustness, frozen holdout, and prospective confirmation. Once the holdout is consumed, it cannot become confirmation data for a candidate created after the holdout.

## Causality

All strategy inputs are normalized events available only after their source bars close. Research returns must shift the resulting exposure by one interval, and execution fills may occur no earlier than the next native bar open. This prevents same-bar hindsight profit attribution.

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

Candidate A/B evidence is measured on paired divergence segments—the intervals where the one changed permission produces different states. Results are also aggregated by continuous bearish regime episode as the higher-level replication unit. Formal support is not eligible until a preregistered minimum amount of genuinely new forward evidence accumulates.

## Execution and paper simulation

A separate execution layer applies next-open fills, fees, and adverse slippage assumptions without altering strategy permission. A deterministic paper-shadow engine uses data hashes, state hashes, idempotent replay, and hard failure on silent historical corrections.

## Current conclusion

The project demonstrates research discipline and engineering architecture, not validated trading alpha. The central unresolved requirement is independent prospective market evidence.

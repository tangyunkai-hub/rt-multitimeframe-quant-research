# Current Research Status

This page separates **engineering readiness** from **statistical validation**.

## Status summary

| Gate | Current status | What would change it |
|---|---|---|
| Source/rule formalization | Substantially complete | New higher-authority source evidence |
| State-machine invariants | Passing current audits | Any semantic or causality failure reopens the gate |
| Retrospective robustness | Mixed | Historical evidence is frozen; no rescue tuning |
| Frozen holdout | **FAIL** | Immutable result |
| Candidate B | Frozen hypothesis | Only genuinely new post-freeze evidence can support/reject it prospectively |
| Historical external validation | **Complete; heterogeneous** | Immutable as retrospective external evidence: BTC adverse, ETH supportive |
| Candidate B forward evidence | **Insufficient** | ≥180 days + ≥3 independent Bear divergence epochs + ≥6 divergence segments |
| Long sparse-trend evidence | Insufficient | ≥365 days + ≥6 completed Long campaigns + ≥3 Bull epochs |
| Risk-capital sizing | Benchmarks frozen, unvalidated | Prospective comparison of fixed policies |
| Execution realism | Engine built; historical fixed-stress audit complete | Prospective next-open execution evidence |
| Paper shadow | Infrastructure built | Sustained deterministic live-shadow operation |
| Deployment readiness | **NO** | All relevant statistical, risk, execution, and paper gates must pass |

## Frozen negative evidence

The principal frozen holdout result remains:

- total return: **-21.61%**;
- Sharpe: **-1.15**;
- maximum drawdown: **-38.02%**.

This result is deliberately not overwritten by post-holdout research.

## Candidate B

Candidate B is a post-holdout hypothesis produced after failure attribution. It changes one permission concept only: after a local Short structural invalidation, same-level re-entry signals inside the same continuous Major Bear epoch are treated as probe/diagnostic rather than automatically restoring core Short exposure.

Candidate B is **not validated**. Historical ablation and external historical validation are not prospective confirmation.

## External Historical Validation — 2017–2022

A pre-registered external historical program was frozen before reading Candidate A/B performance. Its permanent classification is `EXTERNAL_HISTORICAL_VALIDATION_NOT_PROSPECTIVE`.

- **BTC:** 26 paired divergence segments across 3 independent Major Bear divergence epochs; total paired delta log B−A ≈ **-0.1701**; 1/3 epochs favor B; `ADVERSE_EXTERNAL_MECHANISM_EVIDENCE`; leave-one-epoch-out is sign-unstable/negative.
- **ETH:** 20 paired divergence segments across 4 independent Major Bear divergence epochs; total paired delta log B−A ≈ **+0.1482**; 3/4 epochs favor B; `EXTERNAL_MECHANISM_SUPPORT`; leave-one-epoch-out remains positive.
- Fixed 0/2/5bp one-way slippage stress does not change either asset's qualitative label.
- Independent epoch counts are small, so no conventional statistical-significance claim is made.

The cross-asset conclusion is **heterogeneous evidence, not uniform replication**. No post-hoc pooled pass/fail rule is introduced, and Candidate B is not changed from these results.

## Candidate B confirmatory gate

Formal prospective Candidate B judgement is not allowed before all three conditions are met:

1. forward duration ≥ **180 days**;
2. independent Major Bear divergence epochs ≥ **3**;
3. A/B divergence segments ≥ **6**.

Primary statistic: paired incremental log-return over A/B divergence intervals.

Higher-level replication unit: continuous Major Bear epoch, not individual re-entry trades.

## Long sparse-trend gate

Long is evaluated independently from Candidate B. Formal Long support requires at minimum:

- forward duration ≥ **365 days**;
- completed Long campaigns ≥ **6**;
- independent Major Bull epochs with completed Long campaigns ≥ **3**;
- total completed Long log-return > 0;
- leave-best-campaign-out total log-return > 0;
- at least two-thirds of qualifying Bull epochs positive.

Open Long campaigns may be reported mark-to-date but do not count as completed confirmation evidence.

## Research governance rules

- consumed historical data cannot be recycled as Candidate B confirmation;
- external historical validation cannot be relabeled as forward/prospective evidence;
- no threshold is retuned because a historical or forward result looks bad;
- any strategy-defining change creates a new candidate/version and a new freeze boundary;
- multiple trades or segments inside one regime are not treated as independent replications;
- engineering test success is necessary but never sufficient for deployment;
- negative experiments remain in the record.

## Current one-line conclusion

**Research-only. The frozen holdout failed; external historical evidence is cross-asset heterogeneous; Candidate B remains frozen and unvalidated; deployment is not authorized.**

# Current Research Status

This page separates **engineering readiness** from **statistical validation**.

## Status summary

| Gate | Current status | What would change it |
|---|---|---|
| Source/rule formalization | Substantially complete | New higher-authority source evidence |
| State-machine invariants | Passing current audits | Any semantic or causality failure reopens the gate |
| Retrospective robustness | Mixed | Historical evidence is frozen; no rescue tuning |
| Frozen holdout | **FAIL** | Immutable result |
| Candidate B | Frozen hypothesis | Only genuinely new post-freeze evidence can support/reject it |
| Candidate B forward evidence | **Insufficient** | ≥180 days + ≥3 independent Bear divergence epochs + ≥6 divergence segments |
| Long sparse-trend evidence | Insufficient | ≥365 days + ≥6 completed Long campaigns + ≥3 Bull epochs |
| Risk-capital sizing | Benchmarks frozen, unvalidated | Prospective comparison of fixed policies |
| Execution realism | Engine built | Prospective next-open execution evidence |
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

Candidate B is **not validated**. Historical ablation is development/diagnostic evidence only.

## Candidate B confirmatory gate

Formal Candidate B judgement is not allowed before all three conditions are met:

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
- no threshold is retuned because a forward result looks bad;
- any strategy-defining change creates a new candidate/version and a new freeze boundary;
- multiple trades inside one regime are not treated as independent replications;
- engineering test success is necessary but never sufficient for deployment;
- negative experiments remain in the record.

## Current one-line conclusion

**Research-only. Candidate B frozen and prospective-only. Deployment not authorized.**

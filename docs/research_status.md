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
| Cross-exchange execution robustness | **Complete; venue-consistent** | Separate preregistered signal-source recreation would test a different question |
| Candidate B forward evidence | **Insufficient** | ≥180 days + ≥3 independent Bear divergence epochs + ≥6 divergence segments |
| Long sparse-trend evidence | Insufficient | ≥365 days + ≥6 completed Long campaigns + ≥3 Bull epochs |
| Risk-capital sizing | Benchmarks frozen, unvalidated | Prospective comparison of fixed policies |
| Execution realism | Engine built; historical fixed-stress and cross-venue audits complete | Prospective next-open execution evidence |
| Paper shadow | **Engineering hardened, not live** | Sustained deterministic live-shadow operation on genuinely new data |
| Reproducibility | **Hash/manifest verification hardened** | Any provenance failure reopens the gate |
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

## Cross-exchange execution robustness — Coinbase

A separate protocol was frozen before Coinbase strategy performance was read. Frozen Candidate A/B state trajectories were held constant; only the execution/PnL venue changed from Binance Spot to Coinbase Exchange 15m candles. Missing venue bars were not synthesized.

- Coinbase data-only integrity gate: **PASS** for BTC-USD and ETH-USD.
- **BTC:** Candidate B remains `ADVERSE_EXTERNAL_MECHANISM_EVIDENCE`; the locked Binance and Coinbase mechanism signs match at segment and Bear-epoch levels.
- **ETH:** Candidate B remains `EXTERNAL_MECHANISM_SUPPORT`; the locked Binance and Coinbase mechanism signs also match at segment and Bear-epoch levels.
- Frozen 7/9/12bp one-way total-cost scenarios do not flip either asset's mechanism label.
- Result: `CROSS_EXCHANGE_EXECUTION_ROBUSTNESS_NOT_PROSPECTIVE`, with the BTC-adverse / ETH-supportive heterogeneity **execution-venue robust**.

This removes one alternative explanation—single-venue PnL artifacts—but it does not convert old history into prospective confirmation.

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

## v0.28 paper-shadow engineering status

The brokerless paper layer now has explicit audit hardening in addition to the original deterministic runner:

- append-only JSONL audit records chained by SHA-256;
- deterministic state recovery from the full journal;
- bar hash, state-before hash, state-after hash, and record hash verification;
- idempotent identical-bar retry without duplicate journal records;
- hard failure when the same timestamp arrives with changed data, requiring a versioned replay;
- tamper detection if historical journal bytes or stored state are modified;
- stale in-memory state cannot append to a journal whose recovered state differs.

These behaviors are covered by CI across Python 3.10, 3.11, and 3.12. This is **engineering validation only**; paper-shadow market evidence remains not live.

## Reproducibility hardening

Run manifests now reject duplicate basename collisions unless an explicit root is supplied to preserve relative paths. A verifier checks both the manifest self-hash and the current input bytes, so altered inputs or altered manifest metadata fail the provenance audit instead of silently passing.

## Research governance rules

- consumed historical data cannot be recycled as Candidate B confirmation;
- external historical or cross-exchange validation cannot be relabeled as forward/prospective evidence;
- no threshold is retuned because a historical or forward result looks bad;
- any strategy-defining change creates a new candidate/version and a new freeze boundary;
- multiple trades or segments inside one regime are not treated as independent replications;
- confirmed Major direction changes only on an opposite confirmed event; local/provisional evidence may only degrade the regime to `AT_RISK`;
- engineering test success is necessary but never sufficient for deployment;
- negative experiments remain in the record.

## Current one-line conclusion

**Research-only. The frozen holdout failed; external historical evidence is cross-asset heterogeneous but execution-venue robust; Candidate B remains frozen and unvalidated; paper/reproducibility engineering is hardened but not live; deployment is not authorized.**

# Current Research Status

This page separates **engineering readiness** from **statistical validation**. Engineering success does not convert historical or newly collected data into validated alpha.

## Status summary

| Gate | Current status | What would change it |
|---|---|---|
| Source/rule formalization | Substantially complete | New higher-authority source evidence |
| State-machine invariants | Passing current audits | Any semantic or causality failure reopens the gate |
| Retrospective robustness | Mixed | Historical evidence is frozen; no rescue tuning |
| Frozen holdout | **FAIL** | Immutable result |
| Candidate B | Frozen hypothesis | Only genuinely new post-freeze evidence can support/reject it prospectively |
| Historical external validation | **Complete; heterogeneous** | Immutable retrospective evidence: BTC adverse, ETH supportive |
| Cross-exchange execution robustness | **Complete; venue-consistent** | A separate preregistered signal-source experiment would test a different question |
| Independent signal-source recreation | **Blocked by exact native coverage** | New suitable provider coverage or a separately preregistered multi-provider design |
| Post-freeze native-data intake | **Operational; data-only** | Continued successful scheduled intake and provenance checks |
| Candidate B forward evidence | **Insufficient / performance embargoed** | ≥180 days + ≥3 independent Bear divergence epochs + ≥6 divergence segments |
| Long sparse-trend evidence | Insufficient | ≥365 days + ≥6 completed Long campaigns + ≥3 Bull epochs |
| Risk-capital sizing | **Frozen architecture implemented; policies unvalidated** | Prospective side-by-side comparison after Long evidence floor |
| Execution realism | **Engineering hardened; parity-tested** | Prospective next-open execution evidence |
| Paper shadow | **Operationally runnable, not live** | Sustained deterministic shadow operation on genuinely new data |
| Reproducibility | **Hash/manifest verification hardened** | Any provenance failure reopens the gate |
| Deployment readiness | **NO** | All relevant statistical, risk, execution and paper gates must pass |

## Frozen negative evidence

The principal frozen holdout result remains:

- total return: **-21.61%**;
- Sharpe: **-1.15**;
- maximum drawdown: **-38.02%**.

This result is deliberately not overwritten by post-holdout research.

## Candidate B

Candidate B is a post-holdout hypothesis produced after failure attribution. It changes one permission concept only: after a local Short structural invalidation, same-level re-entry signals inside the same continuous Major Bear epoch are treated as probe/diagnostic rather than automatically restoring core Short exposure.

Candidate B is **not validated**. Historical ablation, external history and cross-exchange revaluation are not prospective confirmation.

## External Historical Validation — 2017–2022

The pre-registered external historical program was frozen before reading Candidate A/B performance. Its permanent classification is `EXTERNAL_HISTORICAL_VALIDATION_NOT_PROSPECTIVE`.

- **BTC:** 26 paired divergence segments across 3 independent Major Bear divergence epochs; total paired delta log B−A ≈ **-0.1701**; 1/3 epochs favor B; `ADVERSE_EXTERNAL_MECHANISM_EVIDENCE`.
- **ETH:** 20 paired divergence segments across 4 independent Major Bear divergence epochs; total paired delta log B−A ≈ **+0.1482**; 3/4 epochs favor B; `EXTERNAL_MECHANISM_SUPPORT`.
- Fixed 0/2/5bp one-way slippage stress does not change either asset's qualitative label.
- Independent epoch counts are small, so no conventional statistical-significance claim is made.

The cross-asset conclusion is **heterogeneous evidence, not uniform replication**. No post-hoc pooled pass/fail rule is introduced, and Candidate B is not changed from these results.

## Cross-exchange execution robustness — Coinbase

A separate protocol held frozen Candidate A/B state trajectories constant and moved only execution/PnL from Binance Spot to Coinbase Exchange 15m candles.

- Coinbase data-only integrity gate: **PASS** for BTC-USD and ETH-USD.
- BTC remains `ADVERSE_EXTERNAL_MECHANISM_EVIDENCE`.
- ETH remains `EXTERNAL_MECHANISM_SUPPORT`.
- Segment and Bear-epoch mechanism signs match across venues for both assets.
- Frozen 7/9/12bp one-way total-cost scenarios do not flip either asset's mechanism label.

Result: `CROSS_EXCHANGE_EXECUTION_ROBUSTNESS_NOT_PROSPECTIVE`. This weakens the single-venue-artifact explanation but does not turn old history into prospective confirmation.

## Independent signal-source feasibility

No surveyed single public provider supplied the full exact native clock set required by the frozen compatibility-v3 state engine, including the critical combination of 2h, 8h, 12h, 3d and 1w bars. Because lower-timeframe reconstruction can change authority-critical states, missing clocks are not silently resampled and relabeled as independent native-source replication.

Current status: `BLOCKED_NO_SURVEYED_SINGLE_PROVIDER_EXACT_NATIVE_TIMEFRAME_COVERAGE`.

## Post-freeze native-data operations

Candidate B freeze boundary: **2026-09-12T02:00:00Z**.

The `forward-native-data` GitHub Actions workflow now performs checksum-verified Binance Spot native archive intake with two explicit modes:

- `monitor`: bounded overlap for scheduled source/integrity monitoring; not a complete forward evidence pool;
- `full`: complete frozen-forward rebuild from the preregistered overlap start for audit snapshots.

Hardening rules include:

- closed-bar eligibility is based on availability time, not merely open date;
- Binance post-2025 microsecond epochs and older millisecond epochs are normalized by the frozen magnitude rule;
- a latest requested dense source-day 404 becomes `WAITING_SOURCE_ARCHIVE_PUBLICATION` rather than a stale PASS;
- an older missing dense archive is a hard integrity failure;
- sparse 3d/1w source-day 404s are handled separately because a new native bar does not open every UTC day;
- an independent always-run workflow step requires `performance_evaluation_allowed=false` and `candidate_b_judgement_allowed=false`.

The hardened forward workflow passed run **`34703344067`** and produced artifact `rt-forward-native-data`. At the present early stage this operational success is **not** a prospective performance result.

## Candidate B confirmatory information gate

Formal prospective Candidate B judgement is not allowed before all three frozen conditions are met:

1. forward duration ≥ **180 days**;
2. independent Major Bear divergence epochs ≥ **3**;
3. A/B divergence segments ≥ **6**.

The public `rtquant-prospective-gate` command only counts information. It exposes no threshold-override flags and always returns `performance=null`.

Before the floor is met: `KEEP_PERFORMANCE_EMBARGOED`.

After the floor is met: only `RUN_SEPARATELY_FROZEN_PRIVATE_V024_EVALUATOR` is authorized. The public helper does not substitute its generic evaluator for the frozen private confirmatory protocol.

Primary performance statistic, once legitimately released by that private protocol: paired incremental log-return over intervals where Candidate A and B actually differ. The higher-level replication unit is the continuous Major Bear epoch, not individual re-entry trades.

## Long sparse-trend gate

Long is evaluated independently from Candidate B. Formal Long support requires at minimum:

- forward duration ≥ **365 days**;
- completed Long campaigns ≥ **6**;
- independent Major Bull epochs with completed Long campaigns ≥ **3**;
- total completed Long log-return > 0;
- leave-best-campaign-out total log-return > 0;
- at least two-thirds of qualifying Bull epochs positive.

Open Long campaigns may be reported mark-to-date but do not count as completed confirmation evidence.

## v0.26 risk-capital engineering status

The fixed benchmark family remains frozen and unvalidated; no historical winner is selected. The public package implements only the audit-safe architecture while exact private benchmark sizing recipes remain outside the public repository.

The implementation enforces that risk cannot create exposure from `FLAT`, reductions are applied once, hedge reasons are non-additive, gross caps do not change direction permission, defensive Long logic cannot flip net exposure Short, and the unresolved protective-long mirror for `CORE_SHORT` remains disabled.

This is **engineering readiness only**. P0/P1/P2/P3 remain side-by-side research benchmarks until the v0.25 Long evidence floor is satisfied and the frozen Pareto rule can be applied prospectively.

## v0.27 execution engineering status

The public next-open simulator is fail-closed and mathematically aligned with the incremental v0.28 paper runner:

- a close-known target cannot earn the same bar's return;
- old exposure owns previous-close → next-observed-open gap;
- newly filled exposure owns next-open → close;
- gap, cost and intrabar factors compound sequentially;
- duplicate timestamps, invalid timestamps, non-finite inputs, non-positive prices and invalid costs fail closed;
- an integration invariant requires v0.27 batch equity and v0.28 incremental paper equity to match bar-by-bar under identical costs.

This prevents engineering drift; it does not create prospective execution evidence.

## v0.28 paper-shadow engineering status

The brokerless paper layer now includes a restart-safe operational session around the deterministic runner:

- append-only canonical JSONL audit records chained by SHA-256;
- canonical UTC timestamp and numeric bar identity before hashing;
- explicit journal schema version;
- full-chain recovery once at session start to obtain a verified append cursor;
- single-writer lock with explicit stale-lock recovery policy;
- file-size guard against out-of-band append/truncate after recovery;
- bar hash, state-before hash, state-after hash and record-hash verification;
- non-authoritative checkpoint cache plus session lifecycle log;
- idempotent equivalent-bar retry without duplicate journal records;
- hard failure for changed same-timestamp data, non-monotonic replay or journal tampering.

`rtquant-paper` provides `ingest` and `status` commands but has **no broker or live-order route**. User-visible output uses an allowlist and does not release equity, PnL, return, turnover or future performance-like fields while the prospective embargo is active. Internal equity remains available only for deterministic execution parity and journal verification.

Runtime forward data, private state ledgers and paper journals are gitignored to reduce accidental public disclosure.

This remains **engineering validation only**. Sustained genuinely-new-data paper-shadow evidence is not yet established.

## Reproducibility and CI status

Run manifests reject ambiguous duplicate keys and verify both manifest self-hash and exact current input bytes. Altered inputs or manifest metadata fail the provenance audit instead of silently passing.

The combined engineering suite—including forward-data boundary tests, v0.24 embargo tests, single-writer paper-session tests, brokerless CLI tests and the frozen prospective information-gate CLI—passed on Python **3.10, 3.11 and 3.12** in CI run **`34703631551`** at commit **`dfcb6c898724234419df123eb3b978f2ee6362bc`**.

## Research governance rules

- consumed historical data cannot be recycled as Candidate B confirmation;
- external historical or cross-exchange validation cannot be relabeled as forward/prospective evidence;
- no threshold is retuned because a historical or forward result looks bad;
- the public information-gate CLI cannot lower the frozen evidence floor;
- any strategy-defining change creates a new candidate/version and new freeze boundary;
- multiple trades or segments inside one regime are not treated as independent replications;
- confirmed Major direction changes only on an opposite confirmed event; local/provisional evidence may only degrade the regime to `AT_RISK`;
- risk-policy engineering does not authorize selecting a live policy from consumed historical PnL;
- paper engineering does not authorize live trading;
- engineering test success is necessary but never sufficient for deployment;
- negative experiments remain in the record.

See [`prospective_operations.md`](prospective_operations.md) for the operational runbook.

## Current one-line conclusion

**Research-only. The frozen holdout failed; external historical evidence is cross-asset heterogeneous but execution-venue robust; Candidate B remains frozen and unvalidated; automated forward intake and embargo-safe paper/information-gate tooling are operational, while the required prospective evidence remains insufficient and deployment is not authorized.**

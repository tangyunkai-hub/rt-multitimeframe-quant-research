# Prospective Operations Runbook

This runbook describes the operational boundary between public data intake, the private frozen state engine, the prospective information gate, and the brokerless paper journal. It does **not** authorize strategy retuning or performance inspection.

## 1. Public forward native-data intake

The `forward-native-data` GitHub Actions workflow collects checksum-verified Binance Spot native archives after the Candidate B freeze boundary (`2026-09-12T02:00:00Z`). It is data-only: `performance_evaluation_allowed=false` and `candidate_b_judgement_allowed=false` are enforced by a separate always-run workflow step.

Two collection modes are deliberately different:

- `monitor` is the scheduled bounded-overlap health check. It re-reads only enough history to cover the longest native bar plus one day and must **not** be treated as the complete forward evidence pool.
- `full` rebuilds the complete frozen-forward pool from the preregistered overlap start and is the audit mode to use when a complete data snapshot is required.

Examples:

```bash
python tools/download_forward_native_data.py --mode monitor
python tools/download_forward_native_data.py --mode full --end-date 2026-10-31
```

A dense daily archive missing for the latest requested source day is `WAITING_SOURCE_ARCHIVE_PUBLICATION`, not a PASS based on stale rows. A missing older dense archive is a hard integrity failure. Sparse 3d/1w daily archive 404s are treated separately because those intervals do not open a new native bar every UTC day.

The operational policy also waits until there is a fully completed UTC calendar day after the freeze date before starting the forward pool. With the current freeze boundary, the first fully post-freeze source day is **2026-09-13 UTC**; a scheduled run can only ingest that completed day afterward.

## 2. Private frozen state generation

Exact proprietary signal construction remains outside the public repository. The private frozen engine may consume the verified native data and produce a forward state ledger with only the fields required by the public information-floor counter:

```text
timestamp,A_core,B_core,major_bear_epoch_id
```

The state ledger is operational research material. Keep it under an ignored local path such as `runtime/`; do not commit live forward state or paper journals to the public repository.

## 3. Frozen prospective information gate

After installing the package, run:

```bash
rtquant-prospective-gate --input runtime/candidate_b_forward_states.csv
```

The CLI intentionally exposes **no threshold override flags**. The frozen public floor remains:

- at least 180 forward days;
- at least 6 A/B divergence segments;
- at least 3 independent Major Bear divergence epochs.

Before all three conditions are met, the output keeps `performance=null` and returns `KEEP_PERFORMANCE_EMBARGOED`. When all three are met, the only authorization is `RUN_SEPARATELY_FROZEN_PRIVATE_V024_EVALUATOR`. The public CLI still does not compute Candidate A/B performance.

## 4. Brokerless paper operation

The paper CLI accepts validated CSV/JSONL bars and writes the hash-chained single-writer journal locally:

```bash
rtquant-paper ingest \
  --journal runtime/candidate_b.paper.jsonl \
  --input runtime/paper_bars.csv

rtquant-paper status --journal runtime/candidate_b.paper.jsonl
```

The CLI has no broker or live-order route. User-visible output is allowlisted and does not release equity, PnL, return, turnover, or other performance fields while the prospective embargo is active. Internal deterministic state may still contain the equity field required for execution parity and journal verification; it is not released by the operational CLI.

Equivalent retry of the last processed bar is idempotent. A changed same-timestamp bar, non-monotonic replay, journal tampering, unexpected journal byte change, or concurrent writer causes the operation to fail closed.

## 5. Evidence governance

The operational chain is:

```text
checksum-verified native data
        ↓
private frozen state engine
        ↓
public information-floor counter (no performance)
        ↓
[only after frozen floor is met]
separately frozen private v0.24 evaluator
```

Historical or external validation is never relabeled as prospective evidence. No strategy semantic, threshold, cost convention, or sizing rule may change because of forward performance. Any strategy-defining change creates a new candidate/version and requires a new freeze boundary.

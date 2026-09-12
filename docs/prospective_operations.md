# Prospective Operations Runbook

This runbook separates source collection, consumed-state initialization, the private frozen state engine, the information gate and the brokerless paper journal. It never authorizes strategy retuning or early performance inspection.

## 1. Forward source intake

`forward-native-data` collects two causally distinct sources under the same run cutoff:

- Binance Spot native data: execution/signal source under the frozen architecture;
- Bitstamp BTCUSD 12h/1d: **state-only** higher-timeframe source. `price_pnl_use_allowed=false` is a hard gate.

Both collectors preserve `performance_evaluation_allowed=false` and `candidate_b_judgement_allowed=false`. Formal state production requires `mode=full` and `FULL_REBUILD_COMPLETE_FORWARD_POOL`; `monitor` is only a bounded-overlap health check.

```bash
python tools/download_forward_native_data.py --mode full --out runtime/forward_native_full --end-date 2026-10-31
python tools/download_forward_bitstamp_state.py --mode full --out runtime/forward_native_full --end-date 2026-10-31
```

Missing/stale sources remain WAITING or FAIL; they are never silently filled or interpolated.

## 2. Consumed pre-freeze warm-up seed

Long-memory indicator/state construction cannot begin from a few post-freeze days. A separate data-only workflow therefore builds a seed from data whose availability is **at or before** the Candidate B freeze boundary `2026-09-12T02:00:00Z`.

The seed is classified `V024_CONSUMED_PRE_FREEZE_WARMUP_SEED` and must state:

- performance evaluation disabled;
- Candidate B judgement disabled;
- prospective evidence rows = 0;
- exact file SHA-256 values and a seed-root SHA-256.

The seed only initializes state. No pre-freeze row can enter the released forward state ledger or the v0.24 information counts.

## 3. Private frozen state producer

The proprietary producer stays outside the public repository. Public code commits only its exact SHA-256. The frozen v1 implementation passed consumed semantic regression on 45,807 campaign timestamps with zero authority-critical state/action mismatches; this is implementation evidence, not Alpha evidence.

After the warm-up seed is hash-bound, operational invocation is conceptually:

```bash
rtquant-prospective-intake \
  --private-producer /private/v024_prospective_signal_producer_v1.py \
  --warmup-seed /private/v024_warmup_seed \
  --warmup-contract /private/v024_warmup_seed/WARMUP_SEED_CONTRACT.json
```

The state ledger remains minimal:

```text
timestamp,A_core,B_core,major_bear_epoch_id
```

## 4. Frozen prospective information gate

`rtquant-prospective-gate` has no threshold override flags. Formal v0.24 evaluation remains embargoed until all frozen floors are satisfied: at least 180 forward days, 6 A/B divergence segments and 3 independent Major Bear divergence epochs. Reaching the floor only authorizes the separately frozen private evaluator; it does not auto-declare success.

## 5. Brokerless paper operation

`rtquant-paper` wemains brokerless. Its append-only hash chain, deterministic restart, idempotent retry and changed-history hard failure are engineering controls only. Operational output does not release equity/PnL while the prospective embargo is active.

## 6. Evidence governance

```text
consumed pre-freeze warm-up seed ─┐
post-freeze Binance full source ──┼─> private frozen state producer
post-freeze Bitstamp state-only ──┘              ↓
                                      public information-floor gate
                                                  ↓
                                  [only after frozen floor is met]
                                   frozen private v0.24 evaluator
```

Historical/external evidence is never relabeled as prospective evidence. Bitstamp prices never enter Binance PnL. Any strategy-semantic change requires a new version, freeze and validation pool.

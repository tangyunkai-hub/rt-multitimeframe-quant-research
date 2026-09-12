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

Missing/stale sources remain WAITING or FAIL; they are never silently filled or interpolated. The forward Bitstamp source remains state-only and cannot enter Binance PnL.

The latest verified collector run after the Bitstamp syntax fix is GitHub Actions run `34724787426`, whose collect and enforcement steps both passed. At that run time there was not yet a fully completed post-freeze UTC source day, so both sources correctly reported `WAITING_NO_COMPLETED_POST_FREEZE_UTC_DAY`.

## 2. Consumed pre-freeze warm-up seed

Long-memory indicator/state construction cannot begin from a few post-freeze days. A separate data-only workflow therefore freezes a seed from data whose availability is **at or before** the Candidate B freeze boundary `2026-09-12T02:00:00Z`.

The frozen seed is classified `V024_CONSUMED_PRE_FREEZE_WARMUP_SEED` and is now byte-bound:

- contract SHA-256: `a252b31f29bc7604225d482b9ec394c58360145f2ab57368e80860958da33085`
- seed-root SHA-256: `4d5233007551a282164a40cdb34580535454fa07d757666180dc7d83d039589f`
- workflow run: `34723033060`
- artifact: `10306991596`
- prospective evidence rows: `0`

The contract also fixes performance evaluation disabled and Candidate B judgement disabled. The seed only initializes state. No pre-freeze row can enter the released forward state ledger or v0.24 information counts.

## 3. Private frozen state producer

The proprietary producer stays outside the public repository. Public code commits only its exact SHA-256. The frozen v1 implementation passed consumed semantic regression on 45,807 campaign timestamps with zero authority-critical state/action mismatches; this is implementation evidence, not Alpha evidence.

Producer SHA-256:

`c2f2a47cf4a22d975a75c922eec3d0cb6d65664180fdf80246b302ac80ed8ceb`

Operational invocation, once formal full source gates are eligible, is:

```bash
rtquant-prospective-intake \
  --private-producer /private/v024_prospective_signal_producer_v1.py \
  --warmup-seed /private/v024_warmup_seed \
  --warmup-contract /private/v024_warmup_seed/WARMUP_SEED_CONTRACT.json
```

The intake verifies the private producer bytes, warm-up contract/files, Binance source gate/manifest and Bitstamp state-only gate/manifest before producing any state ledger.

The state ledger remains minimal:

```text
timestamp,A_core,B_core,major_bear_epoch_id
```

## 4. Frozen prospective information gate

`rtquant-prospective-gate` has no threshold override flags. Formal v0.24 evaluation remains embargoed until all frozen floors are satisfied: at least 180 forward days, 6 A/B divergence segments and 3 independent Major Bear divergence epochs. Reaching the floor only authorizes the separately frozen private evaluator; it does not auto-declare success.

## 5. Brokerless paper operation

`rtquant-paper` remains brokerless. Its append-only hash chain, deterministic restart, idempotent retry and changed-history hard failure are engineering controls only. Operational output does not release equity/PnL while the prospective embargo is active.

## 6. Evidence governance

```text
frozen consumed warm-up seed ─────┐
post-freeze Binance full source ──┼─> private frozen state producer
post-freeze Bitstamp state-only ──┘              ↓
                                      provenance-bound state ledger
                                                  ↓
                                      public information-floor gate
                                                  ↓
                                  [only after frozen floor is met]
                                   frozen private v0.24 evaluator
```

Historical/external evidence is never relabeled as prospective evidence. Bitstamp prices never enter Binance PnL. Any strategy-semantic change requires a new version, freeze and validation pool. A source WAITING state does not authorize synthetic filling, partial-day promotion, or early performance inspection.

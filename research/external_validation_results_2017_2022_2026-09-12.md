# External Historical Validation Results — 2017–2022

**Classification:** `EXTERNAL_HISTORICAL_VALIDATION_NOT_PROSPECTIVE`  
**Adapter:** frozen implementation-compatibility v3  
**Evaluation protocol:** frozen before external performance was read  
**Status:** valid retrospective external evaluation; **not** prospective confirmation and **not** deployment evidence.

## Governance lock

- Candidate A/B strategy semantics, thresholds, sizing, execution convention, and the 14bp round-trip primary cost were frozen before reading these results.
- The only admissible A/B core divergence remained A=`CORE_SHORT` versus B=`FLAT` after the already-frozen local structural exit condition.
- Any negative evidence is retained. These results cannot be used to rewrite Candidate B or the failed v0.22 holdout.
- All required run-level invariants passed with zero failures for both BTC and ETH.

## Primary results

| Asset | A total return | B total return | A max DD | B max DD | Divergence segments | Bear epochs | Epochs favoring B | Paired Δ log (B−A) | Frozen-rule judgement | LOEO |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| BTC | +975.07% | +806.95% | -36.68% | -43.77% | 26 | 3 | 1/3 | -0.1701 | `ADVERSE_EXTERNAL_MECHANISM_EVIDENCE` | `LOEO_CONCENTRATED_OR_SIGN_UNSTABLE` |
| ETH | -3.37% | +12.07% | -83.90% | -83.90% | 20 | 4 | 3/4 | +0.1482 | `EXTERNAL_MECHANISM_SUPPORT` | `LOEO_ROBUST_POSITIVE` |

### BTC interpretation

BTC meets the preregistered external mechanism evidence floor (history duration, divergence segments, and independent Bear epochs), so its directional label is eligible. Candidate B is **worse** than Candidate A on the frozen paired mechanism test: total paired delta log is negative, only one of three Bear divergence epochs favors B, and leave-one-epoch-out remains sign-unstable/negative. The frozen result is therefore `ADVERSE_EXTERNAL_MECHANISM_EVIDENCE`.

Long core exposure is identical by construction and contributes the same result in A and B. The BTC difference is entirely Short-side permission. Candidate A Short re-entry campaigns compound to about +18.54% in this external sample, while the initial/other Short campaigns shared by both candidates compound to about −10.11%; suppressing those re-entries therefore hurts BTC performance.

### ETH interpretation

ETH also meets the frozen evidence floor. Here the mechanism goes the other way: three of four independent Bear divergence epochs favor B, total paired delta log is positive, and every leave-one-epoch-out recomputation remains positive. The frozen result is `EXTERNAL_MECHANISM_SUPPORT` with `LOEO_ROBUST_POSITIVE`.

On ETH, the shared initial/other Short campaigns compound to about +6.62%, while Candidate A Short re-entry campaigns compound to about −13.77%; suppressing those re-entries helps Candidate B.

## Cross-asset conclusion

The external historical evidence is **heterogeneous across assets**: BTC is adverse to Candidate B while ETH supports it. No post-hoc pooled pass/fail rule is introduced. This is not uniform cross-asset replication and therefore does not justify promoting Candidate B. It also does not justify rewriting Candidate B from the consumed historical evidence. The prospective v0.24 gate remains the decisive confirmation path.

## Execution-stress robustness

The frozen 0/2/5bp one-way slippage scenarios were applied as secondary stress on top of the 7bp one-way baseline cost. The qualitative mechanism labels do not flip:

| Asset | Extra slippage | Total one-way cost | Paired Δ log | Frozen-sign-rule label |
|---|---:|---:|---:|---|
| BTC | 0bp | 7bp | -0.1701 | `ADVERSE_EXTERNAL_MECHANISM_EVIDENCE` |
| BTC | 2bp | 9bp | -0.1597 | `ADVERSE_EXTERNAL_MECHANISM_EVIDENCE` |
| BTC | 5bp | 12bp | -0.1440 | `ADVERSE_EXTERNAL_MECHANISM_EVIDENCE` |
| ETH | 0bp | 7bp | +0.1482 | `EXTERNAL_MECHANISM_SUPPORT` |
| ETH | 2bp | 9bp | +0.1562 | `EXTERNAL_MECHANISM_SUPPORT` |
| ETH | 5bp | 12bp | +0.1682 | `EXTERNAL_MECHANISM_SUPPORT` |

## Statistical robustness boundary

The independent unit remains the continuous Major Bear divergence epoch; segments inside one epoch are **not** treated as independent observations. Exact sign-flip diagnostics therefore have very small sample sizes: BTC has 3 independent epochs and ETH has 4. Two-sided exact sign-flip p-values are about 0.50 for BTC and 0.25 for ETH. These diagnostics do **not** establish conventional statistical significance and are not a new selection gate.

## Secondary side attribution

| Asset | Candidate | Long return | Short return | Campaigns (all) |
|---|---|---:|---:|---:|
| BTC | A | +908.93% | +6.56% | 36 |
| BTC | B | +908.93% | -10.11% | 10 |
| ETH | A | +5.10% | -8.06% | 29 |
| ETH | B | +5.10% | +6.62% | 9 |

## Research-status impact

- v0.22 remains `HOLDOUT_FAIL_NOT_DEPLOYMENT_READY`.
- Candidate B remains `FROZEN_HYPOTHESIS_NOT_VALIDATED`.
- v0.24 remains `INSUFFICIENT_FORWARD_EVIDENCE`; 2017–2022 evidence does not count toward its forward clock or replication floor.
- External Historical Validation 2017–2022 is now **complete** for the frozen BTC primary test and ETH cross-asset replication.
- Cross-asset external evidence is mixed/heterogeneous, so **validated Alpha is not established**.
- `SMALL_CAPITAL_LIVE_ELIGIBLE` is **not** reached.

## Reproducibility anchors

- BTC Binance 15m SHA-256: `c76d7a2aa4c42e1cb037e9c852ca65be0ad87e3644fa9f6a95e2cde823b2184e`
- BTC Bitstamp 12h SHA-256: `9ce13cac4413fc865388397b835682ea30327d07827fd6d53422cb5f68ac4b3f`
- BTC Bitstamp 1d SHA-256: `d4bfa4e460abf970684298d2d17f15875a8bde72b1d1b1d6396bffd71dbe8258`
- ETH Binance 15m SHA-256: `2c53bb81455b1288794490aac50249117a550b67c116d97ac7ec76c7f86e8212`
- ETH Bitstamp 12h SHA-256: `6d4d40bd2d7cd43a636582852dc9241341d08eded27f84f5295b0510746684d7`
- ETH Bitstamp 1d SHA-256: `c16107af6486693820b20f1f3082c8d67925915c24c0ba5f134fd22bdc777e68`

Raw/private strategy event recipes and proprietary thresholds remain outside the public repository.

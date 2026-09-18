# V2 Coinbase governance incident and consumed diagnostic — 2026-09-18

Classification: GOVERNANCE_INCIDENT__OUTCOME_CONSUMED__NOT_FORMAL_V2_VALIDATION

The frozen V2/V3 sequence required the normalized Coinbase daily SHA256 and exact runner hash to be frozen before the single retained V2 performance batch. During the 2026-09-18 14:22 CST continuation, the exact previously frozen Coinbase artifact was recovered and audited, but the local audit/runner script computed candidate outcomes in the same execution before a separate durable pre-outcome freeze artifact was persisted. Therefore this read is NOT admissible as the formal V2 validation and must not be upgraded retroactively.

Source identity:
- GitHub Actions source artifact: workflow run 34699255006 / artifact 10299497700.
- Artifact ZIP SHA256: `8fc7692bd5497a154be6867f79388fde9943ecb7d70ed8b8607b9c3f61403d42` (matches preregistration).
- BTCUSD normalized 15m gzip SHA256: `bd77a2d1b37890d0a9fc7f260cfb139ea1d0671f61696ee3176c5e0b087439e5`.
- Frozen overlap actually audited: 2019-09-08 through 2022-12-31 UTC.
- Causal UTC-daily aggregate: 1,211 daily rows, zero missing calendar days, zero duplicate daily timestamps, positive/valid OHLC envelopes.
- Twelve days contain incomplete native 15m coverage (90–95 observed bars rather than 96); no interpolation was used.
- Normalized daily SHA256: `8483837aca86f434f6e2b5fd4fa21c5627f94fb4b28d794f5a84d5b2eac4d8f6`.
- Local combined audit/runner SHA256: `6b0f2f97ad237258931c329f67762503ec88a7b8abf36a77f0407892e3545fcc`.

Consumed diagnostic outcomes (unchanged Cycle-1 semantics; NOT formal validation):
- TSMOM_120 baseline terminal +102.03%, Sharpe 0.647, MaxDD -75.51%; 28bp-RT +91.87%; 56bp-RT +73.03%.
- VM_TSMOM20 baseline terminal +89.28%, Sharpe 0.931, MaxDD -27.92%; 28bp-RT +75.76%; 56bp-RT +51.53%.

Interpretation:
- Directionally supportive same-calendar Coinbase diagnostic, especially VM_TSMOM20 drawdown-adjusted behavior.
- Because the freeze-before-read gate was not durably separated from the outcome computation, these numbers are consumed evidence only and cannot satisfy formal V2.
- No parameter, signal, execution, cost, or source rule may be changed because of these numbers.

Governance repair:
1. Preserve Coinbase as consumed diagnostic evidence; never relabel it untouched/formal V2.
2. Open a replacement V2b on a genuinely unconsumed alternative BTC venue/source (Kraken preferred if durable historical coverage supports the frozen overlap; otherwise another lawful major venue), with source/mapping/data SHA and runner SHA durably frozen BEFORE any performance read.
3. Run unchanged TSMOM_120 and VM_TSMOM20 once on V2b; retain both outcomes and cost stresses.
4. Continue Cycle-2 independent-family preregistration/data audits in parallel.
5. `Validated Alpha = NO` remains unchanged.

# V1 pre-2019 BTC spot — durable source addendum (FROZEN BEFORE PERFORMANCE)

Date: 2026-09-18
Scope: Broad Discovery Cycle-1 Validation Gate V1 only.

## Reason
The already-frozen primary source is Bitstamp BTC/USD daily OHLC through the public Bitstamp API. The current research execution surface could verify the API/documentation but could not durably acquire the full pre-2019 payload. Per the prior source freeze, a lawful source-faithful Bitstamp historical dataset may therefore be used under an addendum, without candidate-driven source selection.

## Frozen fallback source
Use the public GitHub repository `alessiostomeo/btc-cycle-data`, file `bitstamp/1day/BTCUSD_bitstamp_daily_2012-2026.csv`, which documents its Bitstamp series as derived from `ff137/bitstamp-btcusd-minute-data`. The upstream ff137 bulk history is in turn documented as derived from the Zielak/mczielinski Bitstamp historical dataset and licensed CC BY-SA 4.0. This source choice is made solely for durable machine-readable access and is frozen before any V1 candidate signal or performance is computed/read.

## Frozen V1 sample
- Pair: BTC/USD spot, Bitstamp lineage.
- Daily bars: UTC calendar-day OHLCV exactly as supplied by the frozen fallback daily file; no interpolation or discretionary deletion.
- Lower bound: earliest valid daily candle returned by the frozen file.
- Upper bound: 2019-09-07 inclusive; all 2019-09-08 and later rows excluded.
- Preserve all returned days, including zero-volume/flat days if present.

## Frozen engineering gates
Before candidate evaluation persist and verify: source URL/repository/path, Git blob SHA when available, normalized source SHA256, row count, first/last UTC date, unique monotonic dates, explicit calendar-gap count/list, nonpositive OHLC count, invalid OHLC-envelope count. Any failed structural gate stops performance read.

## Frozen candidate mapping
Exactly two already-promoted representatives are evaluated unchanged in one retained batch:
1. `TSMOM_120`: at UTC daily close i, target +1 if close[i] > close[i-120], -1 if lower, else 0. Decision at close i applies from next UTC daily open i+1.
2. `VM_TSMOM20`: base TSMOM20 sign defined identically with 20-day lookback; volatility management is the frozen Cycle-1 implementation: 20 daily log returns through close i, sample standard deviation (ddof=1), annualized sqrt(365), target volatility 20%, leverage=min(2,0.20/vol), target=sign*leverage. Decision at close i applies from next UTC daily open i+1.

Execution/cost semantics remain exactly Cycle-1: next-daily-open execution; daily gross P&L from open[j] to open[j+1] using position[j]=decision[j-1]; turnover=abs(position[j]-position[j-1]); baseline cost 7bp per unit notional turnover per side-equivalent accounting; frozen stress 14bp and 28bp per turnover unit (28/56bp round-trip labels). No stop, threshold, leverage, horizon, filter, or regime modification.

## Frozen interpretation
V1 is genuinely independent-time relative to the Binance USD-M 2019-09-08..2026-09-15 development substrate, but uses BTC spot rather than perpetual futures. Both outcomes must be retained. No parameter selection after V1. Passing V1 is supportive historical validation, not by itself `Validated Alpha = YES`; later V2/V3 and the broader governance matrix remain required. Failure is retained and no rescue tuning is authorized.

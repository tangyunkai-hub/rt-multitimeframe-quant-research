# Portfolio Landing Page

## What this project demonstrates

This project is designed to show quantitative-research judgement, not just Python syntax or a high backtest Sharpe.

### Research skills

- rule formalization from ambiguous discretionary source material;
- evidence hierarchy and model lineage;
- causal multi-timeframe event alignment;
- asymmetric state-machine design;
- campaign-level attribution;
- robustness and concentration diagnostics;
- frozen holdout governance;
- post-failure ablation without data recycling;
- preregistered external historical validation;
- cross-asset and cross-exchange robustness;
- prospective A/B design using paired divergence intervals and regime-level replication;
- explicit separation between retrospective robustness and prospective confirmation.

### Engineering skills

- typed event/state model;
- deterministic state transitions;
- normalized-event validation;
- next-open execution simulation;
- append-only hash-chained paper-shadow audit;
- deterministic restart recovery and tamper detection;
- collision-safe SHA-256 run manifests with verification;
- automated unit/integration/governance tests;
- Python 3.10/3.11/3.12 CI matrix.

## The result I would discuss in an interview

The strongest result is not the historical +257.9% diagnostic. It is the sequence of evidence after that number looked attractive.

The frozen holdout failed materially:

- return: **-21.61%**;
- Sharpe: **-1.15**;
- maximum drawdown: **-38.02%**.

That result became immutable evidence. A single minimal post-holdout Candidate B was then frozen without recycling the failed holdout as confirmation.

A preregistered 2017–2022 external historical test subsequently produced **contradictory cross-asset evidence**: BTC was adverse to Candidate B while ETH was supportive. Revaluing the exact same frozen state paths on Coinbase reproduced the same directional split, showing that the contradiction is not explained by one execution venue. Candidate B was still not changed.

That is the project’s central research story: preserve failure, preserve contradiction, narrow alternative explanations, and wait for genuinely new evidence instead of tuning the answer.

## 90-second narrative

I converted a discretionary multi-timeframe Bitcoin framework into a causal state machine and separated evidence, campaign authority, risk sizing, execution, and paper trading. Retrospective results looked strong, but robustness work showed temporal decay, sparse Long campaigns, fragile Short independence, and parameter sensitivity. I froze the strategy and ran a holdout; it failed materially. Instead of deleting losing components and rerunning the same period, I preserved the failure, performed attribution only, isolated one weakly source-authorized automatic re-entry permission, froze a new Candidate B, and reserved confirmation for genuinely prospective data.

Before reading an older external period, I preregistered a separate retrospective protocol. BTC argued against Candidate B while ETH supported it. I then preregistered a cross-exchange execution test and moved only PnL/execution from Binance to Coinbase; the same BTC/ETH split survived. The repository therefore does not claim validated Alpha. It demonstrates how to build and audit a research program that remains credible when the evidence is inconvenient.

## Current boundary

- Candidate B: frozen, unvalidated.
- v0.24 Short prospective gate: insufficient forward evidence.
- v0.25 Long gate: frozen, insufficient evidence.
- v0.26 risk-capital policies: frozen, unvalidated.
- v0.27 execution layer: built and retrospectively stress-tested, not prospectively validated.
- v0.28 paper-shadow: engineering hardened, not live.
- small-capital live eligibility: **false**.

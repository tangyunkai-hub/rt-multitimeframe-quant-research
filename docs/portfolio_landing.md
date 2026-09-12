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
- prospective A/B design using paired divergence intervals and regime-level replication.

### Engineering skills

- typed event/state model;
- deterministic state transitions;
- normalized-event validation;
- next-open execution simulation;
- restart-safe paper-shadow processing;
- immutable SHA-256 run manifests;
- automated unit/integration tests;
- CI-ready package structure.

## The result I would discuss in an interview

The strongest result is not the historical +257.9% diagnostic. It is the fact that the frozen holdout failed, and the research process did not hide or optimize away that failure.

The failed holdout produced roughly:

- return: **-21.61%**;
- Sharpe: **-1.15**;
- maximum drawdown: **-38.02%**.

That result became immutable evidence. The next candidate was defined by a single minimal permission change and all consumed data were embargoed from confirmatory use.

## 90-second narrative

I converted a discretionary multi-timeframe Bitcoin framework into a causal state machine and separated evidence, campaign authority, risk sizing, execution, and paper trading. Retrospective results looked strong, but robustness work showed temporal decay, sparse Long campaigns, fragile Short independence, and parameter sensitivity. I froze the strategy and ran a holdout. It failed materially. Instead of deleting losing components and rerunning the same period, I preserved the failure, performed attribution only, isolated one weakly source-authorized automatic re-entry permission, froze a new candidate, and moved confirmation to genuinely prospective data. The repository shows the research controls and engineering needed to make that process reproducible.

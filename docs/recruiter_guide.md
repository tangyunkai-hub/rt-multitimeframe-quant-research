# Recruiter / Reviewer Guide

This page is designed for a fast first-pass review of the repository.

## 30-second summary

This project converts a discretionary multi-timeframe Bitcoin framework into a causal quantitative-research system with explicit evidence authority, frozen holdout governance, post-failure attribution, preregistered external/cross-exchange robustness, prospective A/B validation, next-open execution, deterministic paper-shadow auditing, and SHA-256 reproducibility controls.

The most important result is **not a successful backtest**. The frozen holdout failed, and later external evidence remained contradictory: BTC was adverse to Candidate B while ETH was supportive. Moving the frozen state paths from Binance to Coinbase execution reproduced the same split. The project preserves those results instead of tuning them away.

## What to inspect in five minutes

### 1. Research judgement

Read the top of [`README.md`](../README.md) and [`research_status.md`](research_status.md).

The immutable frozen holdout was roughly:

- **-21.61% return**;
- **-1.15 Sharpe**;
- **-38.02% max drawdown**.

The failed period is not reused as confirmation data for the modified candidate.

### 2. Contradictory external evidence

Read [`external_validation_results_2017_2022_2026-09-12.md`](../research/external_validation_results_2017_2022_2026-09-12.md) and [`cross_exchange_execution_results_2017_2022_2026-09-12.md`](../research/cross_exchange_execution_results_2017_2022_2026-09-12.md).

The same frozen Candidate B mechanism is adverse on BTC and supportive on ETH. A separately frozen Coinbase execution replication preserves that direction on both assets. This narrows one alternative explanation without converting old history into prospective evidence.

### 3. State-machine engineering

Review [`src/rtquant/core/`](../src/rtquant/core/).

Look for persistent confirmed regime authority, local risk states separated from reversal, explicit re-entry-watch state, and Candidate A/B permission differences encoded as state transitions rather than hidden filters.

### 4. Causal validation and execution

Review [`src/rtquant/validation/`](../src/rtquant/validation/) and [`src/rtquant/execution/`](../src/rtquant/execution/).

The design prevents a signal known at bar close from earning the same bar's return. The execution layer uses next-observed-open semantics and explicit fixed cost/slippage scenarios.

### 5. Paper audit and reproducibility

Review [`src/rtquant/paper/`](../src/rtquant/paper/), [`src/rtquant/repro/`](../src/rtquant/repro/), and [`tests/`](../tests/).

The paper layer uses an append-only hash chain, deterministic restart replay, idempotency, changed-history hard failure, and tamper detection. Run manifests fail closed on ambiguous keys and verify both metadata provenance and exact input bytes. CI runs across Python 3.10, 3.11, and 3.12.

### 6. Research narrative

Read [`research/RT_Quant_Research_Public_Technical_Paper.md`](../research/RT_Quant_Research_Public_Technical_Paper.md).

The paper explains why strong retrospective performance did not justify deployment, how the holdout failed, why the post-holdout modification was intentionally minimal, what the contradictory external evidence means, and why genuinely new market data are still required.

## Skills demonstrated

### Quant research

- discretionary-rule formalization;
- causal multi-timeframe alignment;
- event/campaign attribution;
- temporal and cost robustness analysis;
- contribution concentration analysis;
- holdout governance;
- ablation after failure without data recycling;
- cross-asset and cross-exchange replication;
- paired prospective A/B design;
- regime-level independence reasoning;
- explicit control of retrospective versus prospective evidence.

### Research engineering

- Python package structure;
- deterministic state machines;
- schema validation;
- next-open execution simulation;
- restart-safe and tamper-evident paper replay;
- versioned hash journals;
- run manifests and byte verification;
- unit/integration/governance testing;
- GitHub Actions CI.

## Interview question this project is meant to answer

> “Can you show me a research project where the evidence went against your original hypothesis, and explain how you avoided overfitting the next version?”

A strong answer is the chain: v0.22 frozen holdout failure → minimal Candidate B freeze → BTC external adverse evidence versus ETH support → venue-robust contradiction → no rescue tuning → prospective gate remains waiting.

## What this repository intentionally does not claim

It does not claim validated alpha, production readiness, an optimal risk allocation, a complete public trading recipe, institutional capacity, or live execution performance. The repository is intended to demonstrate **research quality and engineering discipline**, not to market a finished trading product.

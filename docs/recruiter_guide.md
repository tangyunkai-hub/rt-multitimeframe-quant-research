# Recruiter / Reviewer Guide

This page is designed for a fast first-pass review of the repository.

## 30-second summary

This project converts a discretionary multi-timeframe Bitcoin framework into a causal quantitative-research system with:

- explicit source/evidence authority;
- an event-driven campaign state machine;
- closed-bar causality;
- asymmetric Long/Short permissions;
- frozen holdout governance;
- post-failure attribution;
- prospective A/B validation;
- next-open execution simulation;
- deterministic paper-shadow replay;
- SHA-256 reproducibility manifests;
- automated CI tests.

The most important result is a **failed frozen holdout**, not a successful backtest.

## What to inspect in five minutes

### 1. Research judgement

Read the top of [`README.md`](../README.md) and [`research_status.md`](research_status.md).

The project explicitly preserves a frozen holdout of roughly:

- **-21.61% return**;
- **-1.15 Sharpe**;
- **-38.02% max drawdown**.

The failed period is not reused as confirmation data for the modified candidate.

### 2. State-machine engineering

Review [`src/rtquant/core/`](../src/rtquant/core/).

Look for:

- persistent confirmed regime authority;
- local risk states separated from regime reversal;
- explicit re-entry-watch state;
- Candidate A/B permission differences encoded as state transitions rather than hidden filters.

### 3. Causal validation

Review [`src/rtquant/validation/`](../src/rtquant/validation/) and [`src/rtquant/execution/`](../src/rtquant/execution/).

The design prevents a signal known at bar close from earning the same bar's return. The execution layer uses next-open semantics.

### 4. Reproducibility

Review [`src/rtquant/repro/`](../src/rtquant/repro/) and [`tests/`](../tests/).

Forward runs are designed to record code/protocol/data fingerprints so that a later result can be traced back to the exact version that produced it.

### 5. Research narrative

Read [`research/RT_Quant_Research_Public_Technical_Paper.md`](../research/RT_Quant_Research_Public_Technical_Paper.md).

The paper explains why a strong retrospective path did not justify deployment, how the holdout failed, why the post-holdout modification was intentionally minimal, and why new data are required before making a new performance claim.

## Skills demonstrated

### Quant research

- discretionary-rule formalization;
- causal multi-timeframe alignment;
- event/campaign attribution;
- temporal robustness analysis;
- contribution concentration analysis;
- holdout governance;
- ablation after failure without data recycling;
- paired prospective A/B design;
- regime-level independence reasoning.

### Research engineering

- Python package structure;
- deterministic state machines;
- schema validation;
- next-open execution simulation;
- restart-safe paper replay;
- run manifests and hashes;
- unit/integration testing;
- GitHub Actions CI.

## Interview question this project is meant to answer

> “Can you show me a research project where the result went against your original hypothesis, and explain how you avoided overfitting the next version?”

The answer is the v0.22 holdout failure and the prospective-only Candidate B workflow.

## What this repository intentionally does not claim

It does not claim:

- validated alpha;
- production readiness;
- an optimal risk allocation;
- a complete public trading recipe;
- institutional capacity;
- live execution performance.

The repository is intended to demonstrate **research quality and engineering discipline**, not to market a finished trading product.

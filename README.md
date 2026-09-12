# RT Quant Research — Public Portfolio Release Candidate

A research-engineering portfolio that shows how a discretionary multi-timeframe trading framework was converted into a causal, versioned, testable quantitative research system.

> **Research status:** NOT deployment-ready. A frozen performance holdout failed. The post-holdout candidate remains a prospective hypothesis and is not presented as validated alpha.

## 30-second project snapshot

- Formalized discretionary multi-timeframe logic into an event-driven state machine.
- Enforced completed-bar causality and next-open execution semantics.
- Ran temporal robustness, concentration, cost, delay, and sensitivity diagnostics.
- Preserved a failed frozen holdout: **-21.61% return, -1.15 Sharpe, -38.02% max drawdown**.
- Performed attribution without reusing the failed holdout as confirmation data.
- Froze one minimal post-holdout candidate and moved validation to genuinely new market data.
- Built deterministic paper-shadow, hash manifests, schema validation, and automated tests.

## Why this repository is public-safe

The private research tree contains source notes, exact indicator recipes, internal timeframe labels, and proprietary sizing experiments. This public release intentionally abstracts those details.

What remains public:

- research methodology;
- state-machine architecture;
- causal execution conventions;
- negative-result preservation;
- paired prospective validation design;
- reproducibility and audit tooling;
- synthetic examples and tests.

What is intentionally omitted or abstracted:

- proprietary indicator construction;
- exact signal thresholds;
- private source notes and exports;
- exact internal timeframe/event labels;
- detailed risk-sizing fractions;
- broker credentials or live order routing.

## Evidence timeline

| Stage | Purpose | Status |
|---|---|---|
| Development | Rule formalization + retrospective diagnostics | Complete |
| Robustness | Temporal, campaign, parameter, cost, delay stress | Mixed |
| Frozen holdout | Test unchanged candidate | **FAIL** |
| Failure attribution | Explain failure without rescue tuning | Complete |
| Candidate B | One minimal permission change | Frozen, unvalidated |
| Prospective validation | New-data-only A/B comparison | Waiting for evidence |
| Execution / paper | Causal simulator + deterministic shadow | Engineering-ready only |

## Repository map

```text
src/rtquant/
  core/          Generic campaign state machine + public Candidate B demo
  io/            Normalized-event schema validation
  validation/    Paired A/B divergence evaluation
  execution/     Next-open causal execution simulator
  paper/         Idempotent paper-shadow runner
  repro/         SHA-256 run manifest tooling

docs/            Architecture, methods, reproducibility, portfolio landing page
research/        Public technical paper
examples/        Synthetic bars/events only
tests/           Unit/integration tests
.github/          CI workflow
```

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest -q
python examples/run_synthetic_demo.py
```

The demo uses synthetic data and generic events. It is not a trading signal generator.

## Core research principle

A good historical result is not a validation result. The project deliberately preserves the failed holdout and forbids post-hoc changes from being called validated on the same consumed data.

## Read next

- [Portfolio landing page](docs/portfolio_landing.md)
- [Research methodology](docs/methodology.md)
- [Architecture](docs/architecture.md)
- [Reproducibility](docs/reproducibility.md)
- [Public-release scope](docs/public_release_scope.md)
- [Technical paper](research/RT_Quant_Research_Public_Technical_Paper.md)
- [Interview brief](docs/interview_brief.md)

## Disclaimer

This repository is a research and portfolio artifact, not investment advice, a signal service, or a live trading system.

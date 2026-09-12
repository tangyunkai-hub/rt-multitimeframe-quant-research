# Public RC2 Release Notes

## Purpose

RC2 improves the public portfolio and reviewer experience without changing strategy logic, candidate semantics, or research conclusions.

This remains a **public-safe portfolio view** of the RT Quant Research project, not the private research source tree.

## What changed from RC1

- redesigned the README as a recruiter/researcher landing page;
- added CI, Python-version, research-status, and validation badges;
- added a public Mermaid architecture diagram;
- added a five-minute code-review path;
- added an explicit research-status / unresolved-gates page;
- added a recruiter/reviewer guide;
- clarified Candidate B and Long prospective evidence floors;
- bumped package metadata to `0.1.0rc2`.

## Included

- generic multi-timeframe campaign state machine;
- public abstraction of the one-permission Candidate B hypothesis;
- normalized-event validation;
- paired A/B divergence evaluation;
- next-open execution simulator;
- idempotent paper-shadow runner;
- SHA-256 run manifests;
- synthetic examples;
- automated tests and GitHub Actions CI;
- public technical research summary and interview materials.

## Intentionally omitted

- original discretionary notes;
- proprietary indicator formulas and exact thresholds;
- exact internal timeframe names and event recipes;
- private market exports and screenshots;
- detailed risk-sizing fractions;
- live broker routing or credentials.

## Research status

- frozen holdout: **FAIL**;
- post-holdout Candidate B: **frozen, not validated**;
- prospective evidence: **insufficient**;
- deployment readiness: **NO**.

The frozen holdout remains approximately:

- return: **-21.61%**;
- Sharpe: **-1.15**;
- maximum drawdown: **-38.02%**.

RC2 is a presentation and documentation release. It does not reinterpret, retune, or rescue any strategy result.

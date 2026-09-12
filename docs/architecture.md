# Public Architecture

```mermaid
flowchart LR
    A[Private source evidence] --> B[Normalized closed-bar events]
    B --> C[Candidate A state machine]
    B --> D[Candidate B state machine]
    C --> E[Causal A/B bar ledger]
    D --> E
    E --> F[Paired divergence evaluator]
    E --> G[Execution simulator]
    G --> H[Paper-shadow runner]
    F --> I[Evidence gate]
    H --> I
    I --> J{Research status}
    J -->|insufficient/fail| K[Research only]
    J -->|future support + independent gates| L[Eligibility review]
```

## Public/private boundary

The public repository begins at the **normalized event layer**. Exact proprietary indicator construction and signal thresholds remain private.

This boundary is deliberate: reviewers can audit causality, state authority, validation design, execution logic, and reproducibility without receiving the private trading recipe.

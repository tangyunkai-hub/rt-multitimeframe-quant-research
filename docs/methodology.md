# Methodology

## 1. Separate source authority from performance

Rules are classified as source-grounded, engineering operationalizations, or new research hypotheses. A rule is not upgraded in authority because it improves historical PnL.

## 2. Completed-bar causality

Events are accepted only after their source bars close. A state stamped after bar `T` may earn return only from the next return interval or may fill no earlier than the next native open.

## 3. Confirmed-persistent regime invariant

A confirmed directional regime persists until an opposite confirmed event. Local contrary information may degrade the current regime to `AT_RISK`, but does not silently flip direction.

## 4. Asymmetry is allowed

Long and Short permissions are not forced into mirrors. Symmetry must be supported by source authority or prospective evidence, not aesthetic preference.

## 5. Development, holdout, and prospective data are different pools

- development data: rule engineering and diagnostics;
- frozen holdout: unchanged-candidate evaluation;
- consumed holdout: never reused as validation for a post-holdout change;
- prospective data: only source of confirmatory evidence for the new candidate.

## 6. Paired mechanism evaluation

When Candidate A and Candidate B differ by one permission, primary evidence is measured on the exact intervals where their states diverge. Higher-level independence is assessed by continuous market-regime episodes rather than raw trade count.

## 7. Engineering correctness != statistical validity

Passing unit tests, deterministic replay, or causal execution checks is necessary but not sufficient for a deployment claim.

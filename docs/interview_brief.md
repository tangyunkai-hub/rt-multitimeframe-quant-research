# Interview Brief

## 30-second answer

I converted a discretionary multi-timeframe Bitcoin framework into an auditable event-driven research system. I separated rule authority from risk sizing and execution, enforced closed-bar causality, ran robustness tests, and then froze the candidate for a holdout. The holdout failed by about 21.6% with a 38% max drawdown. I preserved the failure, attributed it without retuning the same period, isolated one minimal post-holdout hypothesis, and moved all confirmation to prospective data.

## Why this matters

The project demonstrates how I handle model risk, data leakage, sparse campaigns, nonstationarity, post-holdout changes, execution realism, and reproducibility—not just how I optimize a backtest.

## Questions I expect

**Why not remove the losing component and rerun?**  
Because the holdout would become development data for the altered candidate. The altered candidate requires new unseen confirmation.

**How do you avoid look-ahead?**  
Events become actionable only after completed bars. New targets earn no same-bar return and execute no earlier than the next native open.

**Why paired A/B intervals?**  
The candidates are identical most of the time. Paired divergence intervals isolate the economic consequence of the one changed permission.

**Why not count each trade as independent?**  
Several trades can occur inside one continuous regime episode. Regime episodes are reported as the higher-level replication unit.

import numpy as np
import pandas as pd


def simulate_next_open(
    df: pd.DataFrame,
    *,
    fee_bps_one_way=7.0,
    slippage_bps_one_way=0.0,
):
    """Causally execute close-known targets at the next observed open.

    The old exposure owns the gap from the previous observed close to the next
    observed open.  The newly filled exposure owns the following open-to-close
    move.  Those wealth legs and transaction cost are compounded sequentially,
    not added as simple-return approximations.
    """
    req = {"timestamp", "open", "close", "target_exposure"}
    miss = req - set(df.columns)
    if miss:
        raise ValueError(f"missing columns: {sorted(miss)}")
    if fee_bps_one_way < 0 or slippage_bps_one_way < 0:
        raise ValueError("cost assumptions must be non-negative")

    x = df.copy()
    x["timestamp"] = pd.to_datetime(x["timestamp"], utc=True, errors="coerce")
    if x["timestamp"].isna().any():
        raise ValueError("invalid timestamp")
    x = x.sort_values("timestamp", kind="mergesort").reset_index(drop=True)
    if x["timestamp"].duplicated().any():
        raise ValueError("duplicate timestamp")

    for col in ("open", "close", "target_exposure"):
        x[col] = pd.to_numeric(x[col], errors="coerce")
    if not np.isfinite(x[["open", "close", "target_exposure"]].to_numpy(dtype=float)).all():
        raise ValueError("non-finite execution input")
    if (x[["open", "close"]] <= 0).any().any():
        raise ValueError("open/close prices must be positive")

    held = x["target_exposure"].astype(float).shift(1, fill_value=0.0)
    turnover = held.diff().abs()
    turnover.iloc[0] = abs(float(held.iloc[0]))
    cost_rate = turnover * (fee_bps_one_way + slippage_bps_one_way) / 10000.0
    if (cost_rate >= 1.0).any():
        raise ValueError("transaction cost consumes all capital on a bar")

    n = len(x)
    gap_component = np.zeros(n, dtype=float)
    intrabar_component = np.zeros(n, dtype=float)
    gross_factor = np.ones(n, dtype=float)
    net_return = np.zeros(n, dtype=float)
    equity = np.ones(n, dtype=float)

    for i in range(1, n):
        old = float(held.iloc[i - 1])
        new = float(held.iloc[i])
        prev_close = float(x["close"].iloc[i - 1])
        op = float(x["open"].iloc[i])
        cl = float(x["close"].iloc[i])

        gap_component[i] = old * (op / prev_close - 1.0)
        intrabar_component[i] = new * (cl / op - 1.0)
        gap_factor = 1.0 + gap_component[i]
        trade_factor = 1.0 - float(cost_rate.iloc[i])
        intrabar_factor = 1.0 + intrabar_component[i]
        if gap_factor < 0 or intrabar_factor < 0:
            raise ValueError("exposure/price move implies negative wealth factor")

        gross_factor[i] = gap_factor * intrabar_factor
        step_factor = gap_factor * trade_factor * intrabar_factor
        net_return[i] = step_factor - 1.0
        equity[i] = equity[i - 1] * step_factor

    out = x.copy()
    out["held_exposure"] = held
    out["turnover"] = turnover
    out["trade_cost"] = cost_rate
    out["gap_return_component"] = gap_component
    out["intrabar_return_component"] = intrabar_component
    out["gross_factor"] = gross_factor
    out["net_return"] = net_return
    out["equity"] = equity
    return out

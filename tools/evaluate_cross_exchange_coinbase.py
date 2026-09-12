from __future__ import annotations

from pathlib import Path
import argparse
import hashlib
import json
import math

import numpy as np
import pandas as pd

CLASSIFICATION = "CROSS_EXCHANGE_EXECUTION_ROBUSTNESS_NOT_PROSPECTIVE"
ANN15 = 96 * 365.25
LOCKED_BINANCE = {
    "BTC": "ADVERSE_EXTERNAL_MECHANISM_EVIDENCE",
    "ETH": "EXTERNAL_MECHANISM_SUPPORT",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def load_timeline(path: Path) -> pd.DataFrame:
    z = pd.read_csv(path)
    z["timestamp"] = pd.to_datetime(z["timestamp"], utc=True, format="mixed")
    z = z.sort_values("timestamp").drop_duplicates("timestamp", keep="last").set_index("timestamp")
    for c in ["core_side", "major_direction"]:
        z[c] = pd.to_numeric(z[c], errors="raise").astype(int)
    if "major_at_risk" in z:
        z["major_at_risk"] = (
            z["major_at_risk"].astype(str).str.lower().map({"true": True, "false": False}).fillna(False).astype(bool)
        )
    else:
        z["major_at_risk"] = False
    return z


def load_coinbase(path: Path) -> pd.DataFrame:
    x = pd.read_csv(path)
    x["open_time"] = pd.to_datetime(x.open_time, utc=True, format="mixed")
    x["availability_time"] = pd.to_datetime(x.availability_time, utc=True, format="mixed")
    for c in ["open", "high", "low", "close", "volume"]:
        x[c] = pd.to_numeric(x[c], errors="raise").astype(float)
    x = x.sort_values("open_time").drop_duplicates("open_time", keep="last").reset_index(drop=True)
    if x.open_time.duplicated().any() or not x.open_time.is_monotonic_increasing:
        raise RuntimeError("Coinbase chronology integrity failure")
    if (x[["open", "high", "low", "close"]] <= 0).any().any():
        raise RuntimeError("Coinbase nonpositive price")
    if ((x.high < x[["open", "close"]].max(axis=1)) | (x.low > x[["open", "close"]].min(axis=1)) | (x.high < x.low)).any():
        raise RuntimeError("Coinbase OHLC envelope failure")
    return x


def structural_invariants(a: pd.DataFrame, b: pd.DataFrame) -> pd.DataFrame:
    idx = a.index.union(b.index).sort_values()
    aa = a.reindex(idx, method="ffill")
    bb = b.reindex(idx, method="ffill")
    ac = aa.core_side.fillna(0).astype(int)
    bc = bb.core_side.fillna(0).astype(int)
    rows = [
        ("major_direction_identical", int((aa.major_direction.fillna(0).astype(int) != bb.major_direction.fillna(0).astype(int)).sum())),
        ("long_core_occupancy_identical", int((ac.eq(1) != bc.eq(1)).sum())),
        ("candidate_b_never_extra_short", int((bc.eq(-1) & ~ac.eq(-1)).sum())),
        ("only_A_short_B_flat_state_divergence", int(((ac != bc) & ~(ac.eq(-1) & bc.eq(0))).sum())),
    ]
    out = pd.DataFrame(rows, columns=["check", "failures"])
    out["status"] = np.where(out.failures.eq(0), "PASS", "FAIL")
    return out


def execute(source: pd.DataFrame, timeline: pd.DataFrame, one_way_bps: float) -> pd.DataFrame:
    x = source[["open_time", "availability_time", "open", "close"]].copy().sort_values("availability_time").reset_index(drop=True)
    q = timeline[["core_side", "major_direction", "major_at_risk"]].reindex(pd.DatetimeIndex(x.availability_time), method="ffill")
    target = q.core_side.fillna(0).astype(float).to_numpy()
    x["target_exposure"] = target
    held = pd.Series(target).shift(1, fill_value=0.0).to_numpy()
    x["held_exposure"] = held
    turnover = np.abs(np.diff(np.r_[0.0, held]))
    x["turnover"] = turnover
    gross = np.zeros(len(x))
    opens = x.open.to_numpy(float)
    closes = x.close.to_numpy(float)
    for i in range(1, len(x)):
        old = held[i - 1]
        new = held[i]
        gross[i] = old * (opens[i] / closes[i - 1] - 1.0) + new * (closes[i] / opens[i] - 1.0)
    cost = turnover * (one_way_bps / 10000.0)
    net = gross - cost
    if np.any(net <= -1):
        raise RuntimeError("invalid net <= -100%")
    x["gross_return"] = gross
    x["trade_cost"] = cost
    x["net_return"] = net
    x["log_net"] = np.log1p(net)
    x["equity"] = np.cumprod(1 + net)
    x["drawdown"] = x.equity / np.maximum.accumulate(x.equity) - 1
    x["major_direction"] = q.major_direction.fillna(0).astype(int).to_numpy()
    x["major_at_risk"] = q.major_at_risk.fillna(False).astype(bool).to_numpy()
    return x


def executed_invariants(a: pd.DataFrame, b: pd.DataFrame) -> pd.DataFrame:
    if len(a) != len(b) or not a.open_time.equals(b.open_time):
        return pd.DataFrame([{"check": "execution_clock_identical", "failures": 1, "status": "FAIL"}])
    rows = [
        ("execution_clock_identical", 0),
        ("executed_major_direction_identical", int(a.major_direction.ne(b.major_direction).sum())),
        ("executed_long_occupancy_identical", int((a.held_exposure.eq(1) != b.held_exposure.eq(1)).sum())),
        ("candidate_b_never_extra_executed_short", int((b.held_exposure.eq(-1) & ~a.held_exposure.eq(-1)).sum())),
        ("only_A_short_B_flat_executed_divergence", int((a.held_exposure.ne(b.held_exposure) & ~(a.held_exposure.eq(-1) & b.held_exposure.eq(0))).sum())),
    ]
    out = pd.DataFrame(rows, columns=["check", "failures"])
    out["status"] = np.where(out.failures.eq(0), "PASS", "FAIL")
    return out


def perf(e: pd.DataFrame) -> dict:
    n = e.net_return.astype(float)
    eq = np.cumprod(1 + n.to_numpy())
    dd = eq / np.maximum.accumulate(eq) - 1
    vol = float(n.std(ddof=1) * math.sqrt(ANN15)) if len(n) > 1 else np.nan
    sharpe = float(n.mean() * ANN15 / vol) if vol and np.isfinite(vol) else np.nan
    return {
        "bars": int(len(n)),
        "total_return": float(eq[-1] - 1) if len(eq) else 0.0,
        "log_return": float(np.log1p(n).sum()),
        "sharpe_0rf": sharpe,
        "max_drawdown": float(dd.min()) if len(dd) else 0.0,
        "turnover_units": float(e.turnover.sum()),
        "cost_drag_sum": float(e.trade_cost.sum()),
        "active_fraction": float((e.held_exposure != 0).mean()),
    }


def divergence(exec_a: pd.DataFrame, exec_b: pd.DataFrame):
    x = exec_a[["open_time", "availability_time", "close", "held_exposure", "log_net", "net_return", "major_direction"]].copy()
    x = x.rename(columns={"held_exposure": "A_exp", "log_net": "A_lognet", "net_return": "A_net"})
    x["B_exp"] = exec_b.held_exposure.to_numpy()
    x["B_lognet"] = exec_b.log_net.to_numpy()
    x["B_net"] = exec_b.net_return.to_numpy()
    bear = x.major_direction.eq(-1)
    starts = bear & ~bear.shift(1, fill_value=False)
    epoch_id = starts.cumsum()
    x["bear_epoch_id"] = np.where(bear, epoch_id, np.nan)
    x["divergent"] = x.A_exp.ne(x.B_exp)
    bad = x.divergent & ~((x.A_exp == -1) & (x.B_exp == 0))
    if bad.any():
        raise RuntimeError("invalid executed A/B divergence")

    segments = []
    active = False
    start = None
    segment_id = 0
    for i, d in enumerate(x.divergent.to_numpy(bool)):
        if d and not active:
            active = True
            start = i
            segment_id += 1
        if active and not d:
            end = i
            sl = x.iloc[start : end + 1]
            ep = x.iloc[start].bear_epoch_id
            delta = float(sl.B_lognet.sum() - sl.A_lognet.sum())
            segments.append({
                "segment_id": segment_id,
                "bear_epoch_id": int(ep) if pd.notna(ep) else None,
                "start": x.iloc[start].open_time,
                "end": x.iloc[end].open_time,
                "bars": int(end - start + 1),
                "A_log_return": float(sl.A_lognet.sum()),
                "B_log_return": float(sl.B_lognet.sum()),
                "paired_delta_log": delta,
                "B_better": bool(delta > 0),
            })
            active = False
    if active:
        end = len(x) - 1
        sl = x.iloc[start : end + 1]
        ep = x.iloc[start].bear_epoch_id
        delta = float(sl.B_lognet.sum() - sl.A_lognet.sum())
        segments.append({
            "segment_id": segment_id,
            "bear_epoch_id": int(ep) if pd.notna(ep) else None,
            "start": x.iloc[start].open_time,
            "end": x.iloc[end].open_time,
            "bars": int(end - start + 1),
            "A_log_return": float(sl.A_lognet.sum()),
            "B_log_return": float(sl.B_lognet.sum()),
            "paired_delta_log": delta,
            "B_better": bool(delta > 0),
        })

    seg = pd.DataFrame(segments)
    epochs = seg.groupby("bear_epoch_id").agg(segments=("segment_id", "count"), paired_delta_log=("paired_delta_log", "sum")).reset_index() if len(seg) else pd.DataFrame(columns=["bear_epoch_id", "segments", "paired_delta_log"])
    if len(epochs):
        epochs["B_better"] = epochs.paired_delta_log > 0
    total = float(seg.paired_delta_log.sum()) if len(seg) else 0.0
    loeo = pd.DataFrame([{"dropped_bear_epoch_id": int(r.bear_epoch_id), "remaining_paired_delta_log": float(total - r.paired_delta_log)} for _, r in epochs.iterrows()])
    duration = (pd.Timestamp(x.availability_time.iloc[-1]) - pd.Timestamp(x.availability_time.iloc[0])).total_seconds() / 86400 if len(x) else 0
    nseg = len(seg)
    nep = len(epochs)
    pos = int(epochs.B_better.sum()) if nep else 0
    neg = nep - pos
    eligible = duration >= 180 and nseg >= 6 and nep >= 3
    if not eligible:
        judgement = "INSUFFICIENT_EXTERNAL_MECHANISM_EVIDENCE"
    elif total > 0 and pos / nep >= 2 / 3:
        judgement = "EXTERNAL_MECHANISM_SUPPORT"
    elif total < 0 and neg > nep / 2:
        judgement = "ADVERSE_EXTERNAL_MECHANISM_EVIDENCE"
    else:
        judgement = "MIXED_EXTERNAL_MECHANISM_EVIDENCE"
    loeo_status = "LOEO_ROBUST_POSITIVE" if len(loeo) and float(loeo.remaining_paired_delta_log.min()) > 0 else "LOEO_CONCENTRATED_OR_SIGN_UNSTABLE"
    summary = {
        "eligible_history_days": duration,
        "divergence_segments": int(nseg),
        "major_bear_divergence_epochs": int(nep),
        "total_paired_delta_log": total,
        "positive_epochs": pos,
        "negative_epochs": neg,
        "mechanism_judgement": judgement,
        "loeo_status": loeo_status,
        "loeo_min_remaining_delta": float(loeo.remaining_paired_delta_log.min()) if len(loeo) else None,
        "floor": {"days": 180, "segments": 6, "bear_epochs": 3},
    }
    return x, seg, epochs, loeo, summary


def run(asset: str, coinbase_path: Path, timeline_a_path: Path, timeline_b_path: Path, outdir: Path) -> dict:
    source = load_coinbase(coinbase_path)
    timeline_a = load_timeline(timeline_a_path)
    timeline_b = load_timeline(timeline_b_path)
    outdir.mkdir(parents=True, exist_ok=True)
    state_inv = structural_invariants(timeline_a, timeline_b)
    state_inv.to_csv(outdir / f"{asset.lower()}_state_invariants.csv", index=False)
    if state_inv.failures.sum() > 0:
        raise SystemExit(f"{asset}: state invariant failure before performance")

    stress = []
    primary = None
    for cost in [7.0, 9.0, 12.0]:
        exec_a = execute(source, timeline_a, cost)
        exec_b = execute(source, timeline_b, cost)
        exec_inv = executed_invariants(exec_a, exec_b)
        if exec_inv.failures.sum() > 0:
            exec_inv.to_csv(outdir / f"{asset.lower()}_execution_invariants_{cost:g}bp.csv", index=False)
            raise SystemExit(f"{asset}: execution invariant failure")
        paired, segments, epochs, loeo, mechanism = divergence(exec_a, exec_b)
        judgement = mechanism["mechanism_judgement"]
        if judgement == "INSUFFICIENT_EXTERNAL_MECHANISM_EVIDENCE":
            venue_consistency = "VENUE_EVIDENCE_INSUFFICIENT"
        else:
            venue_consistency = "VENUE_CONSISTENT" if judgement == LOCKED_BINANCE[asset] else "VENUE_SENSITIVE"
        rec = {
            "asset": asset,
            "venue": "Coinbase",
            "one_way_cost_bps": cost,
            "candidate_A": perf(exec_a),
            "candidate_B": perf(exec_b),
            "mechanism": mechanism,
            "locked_binance_label": LOCKED_BINANCE[asset],
            "venue_consistency": venue_consistency,
        }
        stress.append(rec)
        if cost == 7.0:
            primary = rec
            exec_a.to_csv(outdir / f"{asset.lower()}_candidateA_coinbase_execution_15m.csv", index=False)
            exec_b.to_csv(outdir / f"{asset.lower()}_candidateB_coinbase_execution_15m.csv", index=False)
            exec_inv.to_csv(outdir / f"{asset.lower()}_execution_invariants_7bp.csv", index=False)
            segments.to_csv(outdir / f"{asset.lower()}_paired_segments_coinbase.csv", index=False)
            epochs.to_csv(outdir / f"{asset.lower()}_bear_epochs_coinbase.csv", index=False)
            loeo.to_csv(outdir / f"{asset.lower()}_loeo_coinbase.csv", index=False)
            paired.to_csv(outdir / f"{asset.lower()}_paired_ledger_coinbase.csv", index=False)

    result = {
        "classification": CLASSIFICATION,
        "asset": asset,
        "coinbase_source_sha256": sha256(coinbase_path),
        "timeline_A_sha256": sha256(timeline_a_path),
        "timeline_B_sha256": sha256(timeline_b_path),
        "primary": primary,
        "stress": stress,
        "anti_overfit": "No signal/state/threshold/sizing/cost protocol change permitted from venue results; not prospective evidence.",
    }
    (outdir / f"{asset}_COINBASE_CROSS_EXCHANGE_SUMMARY.json").write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--coinbase-dir", required=True)
    ap.add_argument("--btc-a", required=True)
    ap.add_argument("--btc-b", required=True)
    ap.add_argument("--eth-a", required=True)
    ap.add_argument("--eth-b", required=True)
    ap.add_argument("--out-dir", default="cross_exchange_coinbase_results")
    args = ap.parse_args()

    coinbase_dir = Path(args.coinbase_dir)
    out = Path(args.out_dir)
    results = [
        run("BTC", coinbase_dir / "BTCUSD_15m_2017-2022.csv.gz", Path(args.btc_a), Path(args.btc_b), out / "btc"),
        run("ETH", coinbase_dir / "ETHUSD_15m_2017-2022.csv.gz", Path(args.eth_a), Path(args.eth_b), out / "eth"),
    ]
    (out / "CROSS_EXCHANGE_COINBASE_SUMMARY.json").write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    for r in results:
        p = r["primary"]
        print(r["asset"], p["mechanism"]["mechanism_judgement"], p["venue_consistency"], p["mechanism"]["total_paired_delta_log"])


if __name__ == "__main__":
    main()

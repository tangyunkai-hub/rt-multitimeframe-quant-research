from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

EXPECTED = {"2h": 8, "8h": 32, "72h": 288}
FREQ = {"2h": pd.Timedelta(hours=2), "8h": pd.Timedelta(hours=8), "72h": pd.Timedelta(hours=72)}
OHLC = ["open", "high", "low", "close"]


def truthy(v):
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in {"true", "1", "yes"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_csv(path: Path) -> pd.DataFrame:
    d = pd.read_csv(path)
    d["open_time"] = pd.to_datetime(d["open_time"], format="mixed", utc=True)
    d["availability_time"] = pd.to_datetime(d["availability_time"], format="mixed", utc=True)
    for c in ["open", "high", "low", "close", "volume"]:
        d[c] = pd.to_numeric(d[c], errors="raise").astype(float)
    return d.sort_values("open_time").reset_index(drop=True)


def grid_aligned_15m(ts: pd.Series) -> pd.Series:
    # UTC timestamps exactly on a 15-minute boundary.
    ns = ts.astype("int64")
    step = 15 * 60 * 1_000_000_000
    return (ns % step).eq(0)


def canonical_window_audit(base: pd.DataFrame, symbol: str):
    x = base.copy()
    x["on_15m_grid"] = grid_aligned_15m(x["open_time"])
    x = x.set_index("availability_time").sort_index()

    summaries = []
    invalid_rows = []
    for label, expected in EXPECTED.items():
        freq = FREQ[label]
        count = x["close"].resample(freq, label="right", closed="right", origin="epoch").count()
        grid_count = x["on_15m_grid"].resample(freq, label="right", closed="right", origin="epoch").sum()
        first_open = x["open_time"].resample(freq, label="right", closed="right", origin="epoch").min()
        last_open = x["open_time"].resample(freq, label="right", closed="right", origin="epoch").max()
        agg = x[["open", "high", "low", "close", "volume"]].resample(
            freq, label="right", closed="right", origin="epoch"
        ).agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})

        w = pd.DataFrame({
            "count": count,
            "grid_count": grid_count,
            "first_open": first_open,
            "last_open": last_open,
        }).join(agg, how="left")
        w = w[w["count"].gt(0)].copy()
        w["expected_count"] = expected
        w["complete_count"] = w["count"].eq(expected)
        w["all_on_grid"] = w["grid_count"].eq(w["count"])
        w["valid"] = w["complete_count"] & w["all_on_grid"]

        bad = w[~w["valid"]]
        for t, r in bad.iterrows():
            reason = []
            if not bool(r["complete_count"]):
                reason.append("INCOMPLETE_COUNT")
            if not bool(r["all_on_grid"]):
                reason.append("OFF_GRID_INPUT")
            invalid_rows.append({
                "symbol": symbol,
                "derived_interval": label,
                "availability_time": t,
                "observed_15m_count": int(r["count"]),
                "expected_15m_count": int(expected),
                "on_grid_15m_count": int(r["grid_count"]),
                "first_input_open_time": r["first_open"],
                "last_input_open_time": r["last_open"],
                "reason": "+".join(reason),
            })

        summaries.append({
            "symbol": symbol,
            "derived_interval": label,
            "windows": int(len(w)),
            "valid_windows": int(w["valid"].sum()),
            "invalid_windows": int((~w["valid"]).sum()),
            "incomplete_count_windows": int((~w["complete_count"]).sum()),
            "off_grid_input_windows": int((~w["all_on_grid"]).sum()),
            "valid_rate": float(w["valid"].mean()),
        })
    return summaries, invalid_rows


def manifest_failures(root: Path):
    p = root / "binance_source_manifest.csv"
    if not p.exists():
        return [{"reason": "MISSING_BINANCE_SOURCE_MANIFEST"}]
    m = pd.read_csv(p)
    failures = []
    ok = m[m["status"].eq("ok")].copy()
    if ok.empty:
        return [{"reason": "NO_CHECKSUM_VERIFIED_BINANCE_ARCHIVES"}]
    if "remote_sha256" in ok.columns and "local_sha256" in ok.columns:
        bad = ok[ok["remote_sha256"].astype(str).str.lower() != ok["local_sha256"].astype(str).str.lower()]
        for _, r in bad.iterrows():
            failures.append({"reason": "CHECKSUM_MISMATCH_IN_MANIFEST", "symbol": r.get("symbol"), "interval": r.get("interval"), "month": r.get("month")})
    # A 404 before listing is allowed. A 404 after the first successful month in that series is not.
    for (symbol, interval), g in m.groupby(["symbol", "interval"], dropna=False):
        g = g.sort_values("month")
        good_months = g.loc[g["status"].eq("ok"), "month"]
        if good_months.empty:
            failures.append({"reason": "NO_DATA_FOR_SERIES", "symbol": symbol, "interval": interval})
            continue
        first = good_months.min()
        bad_after = g[(g["month"] >= first) & ~g["status"].eq("ok")]
        for _, r in bad_after.iterrows():
            failures.append({"reason": "MISSING_POST_LISTING_MONTH", "symbol": symbol, "interval": interval, "month": r.get("month"), "status": r.get("status")})
    return failures


def integrity_failures(root: Path):
    p = root / "data_integrity_audit.csv"
    if not p.exists():
        return [{"reason": "MISSING_DATA_INTEGRITY_AUDIT"}]
    d = pd.read_csv(p)
    failures = []
    # Required strategy inputs: Binance 15m and Bitstamp 12h/1d. Native Binance higher TFs are diagnostics.
    required = d[((d["source"] == "Binance") & (d["interval"] == "15m")) | (d["source"] == "Bitstamp")]
    expected = {("Binance", "BTCUSDT", "15m"), ("Binance", "ETHUSDT", "15m"),
                ("Bitstamp", "BTCUSD", "12h"), ("Bitstamp", "BTCUSD", "1d"),
                ("Bitstamp", "ETHUSD", "12h"), ("Bitstamp", "ETHUSD", "1d")}
    present = {(str(r.source), str(r.symbol), str(r.interval)) for _, r in required.iterrows()}
    for miss in sorted(expected - present):
        failures.append({"reason": "MISSING_REQUIRED_SERIES", "source": miss[0], "symbol": miss[1], "interval": miss[2]})
    for _, r in required.iterrows():
        if int(r.get("duplicate_timestamps", 0)) > 0:
            failures.append({"reason": "DUPLICATE_TIMESTAMPS", **r.to_dict()})
        if not truthy(r.get("monotonic", True)):
            failures.append({"reason": "NON_MONOTONIC_TIMESTAMPS", **r.to_dict()})
        if int(r.get("ohlc_envelope_failures", 0)) > 0:
            failures.append({"reason": "OHLC_ENVELOPE_FAILURE", **r.to_dict()})
    return failures


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="external_history_2017_2022")
    a = ap.parse_args()
    root = Path(a.root)

    hard = manifest_failures(root) + integrity_failures(root)
    summaries = []
    invalid = []
    canonical_files = {}
    for symbol in ["BTCUSDT", "ETHUSDT"]:
        p = root / "binance" / f"{symbol}_15m_2017-2022.csv.gz"
        if not p.exists():
            hard.append({"reason": "MISSING_CANONICAL_15M", "symbol": symbol})
            continue
        base = load_csv(p)
        canonical_files[symbol] = {"path": str(p.relative_to(root)), "sha256": sha256_file(p), "rows": int(len(base))}
        s, bad = canonical_window_audit(base, symbol)
        summaries.extend(s)
        invalid.extend(bad)

    summary_df = pd.DataFrame(summaries)
    invalid_df = pd.DataFrame(invalid)
    summary_path = root / "canonical_feature_window_audit.csv"
    invalid_path = root / "canonical_invalid_feature_windows.csv"
    summary_df.to_csv(summary_path, index=False)
    invalid_df.to_csv(invalid_path, index=False)

    out = {
        "status": "PASS" if not hard else "FAIL",
        "classification": "EXTERNAL_HISTORICAL_VALIDATION_NOT_PROSPECTIVE",
        "canonical_source": "official checksum-verified Binance Spot 15m",
        "canonical_files": canonical_files,
        "hard_source_integrity_failures": len(hard),
        "hard_failures": hard,
        "derived_feature_policy": "2h/8h/72h built causally from canonical 15m; exact count and UTC 15m grid required; invalid windows emit no new signal and state persists; no interpolation or synthetic prices",
        "native_binance_higher_tf_role": "DIAGNOSTIC_ONLY",
        "invalid_feature_windows_are_quarantined": True,
        "feature_window_audit_sha256": sha256_file(summary_path),
        "invalid_window_ledger_sha256": sha256_file(invalid_path),
    }
    (root / "CANONICAL_CHAIN_AUDIT.json").write_text(json.dumps(out, indent=2, default=str))
    print(summary_df.to_string(index=False))
    print(json.dumps(out, indent=2, default=str))
    if hard:
        raise SystemExit("canonical external-data source integrity gate failed")


if __name__ == "__main__":
    main()

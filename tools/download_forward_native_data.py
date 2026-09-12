from __future__ import annotations

import argparse
import hashlib
import io
import json
import urllib.error
import urllib.request
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd


DAILY = "https://data.binance.vision/data/spot/daily/klines"
COLS = [
    "open_time_epoch", "open", "high", "low", "close", "volume",
    "close_time_epoch", "quote_asset_volume", "number_of_trades",
    "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore",
]
TFSEC = {
    "15m": 900,
    "30m": 1800,
    "1h": 3600,
    "2h": 7200,
    "4h": 14400,
    "8h": 28800,
    "12h": 43200,
    "1d": 86400,
    "3d": 259200,
    "1w": 604800,
}
INTERVALS = list(TFSEC)
MICROSECOND_EPOCH_THRESHOLD = 10**14
FROZEN_FORWARD_BOUNDARY = pd.Timestamp("2026-09-12T02:00:00Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "rtquant-forward-data/1.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()


def checksum(text: str) -> str:
    return text.strip().splitlines()[0].replace("*", " ").split()[0].lower()


def parse_spot_epoch(values: pd.Series) -> pd.Series:
    x = pd.to_numeric(values, errors="raise").astype("int64")
    out = pd.Series(pd.NaT, index=x.index, dtype="datetime64[ns, UTC]")
    micro = x.abs() >= MICROSECOND_EPOCH_THRESHOLD
    if (~micro).any():
        out.loc[~micro] = pd.to_datetime(x.loc[~micro], unit="ms", utc=True)
    if micro.any():
        out.loc[micro] = pd.to_datetime(x.loc[micro], unit="us", utc=True)
    return out


def read_zip(blob: bytes) -> pd.DataFrame:
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        names = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if len(names) != 1:
            raise ValueError(f"expected exactly one CSV, got {names}")
        frame = pd.read_csv(io.BytesIO(archive.read(names[0])), header=None, names=COLS)
    for col in ("open_time_epoch", "close_time_epoch", "number_of_trades"):
        frame[col] = pd.to_numeric(frame[col], errors="raise").astype("int64")
    for col in ("open", "high", "low", "close", "volume"):
        frame[col] = pd.to_numeric(frame[col], errors="raise").astype(float)
    return frame


def verified_archive(url: str):
    blob = get(url)
    local = sha256_bytes(blob)
    remote = checksum(get(url + ".CHECKSUM").decode("utf-8", "replace"))
    if local != remote:
        raise RuntimeError(f"checksum mismatch: {url}")
    return read_zip(blob), local


def day_iter(start_day: date, end_day: date):
    current = start_day
    while current <= end_day:
        yield current
        current += timedelta(days=1)


def default_end_date() -> date:
    # Only request fully completed UTC calendar days from the archive.
    return datetime.now(timezone.utc).date() - timedelta(days=1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="forward_native_data")
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--end-date", default=None, help="inclusive UTC YYYY-MM-DD; defaults to yesterday")
    args = parser.parse_args()

    out = Path(args.out)
    data_dir = out / "binance"
    data_dir.mkdir(parents=True, exist_ok=True)

    end_day = date.fromisoformat(args.end_date) if args.end_date else default_end_date()
    if pd.Timestamp(end_day, tz="UTC") <= FROZEN_FORWARD_BOUNDARY.normalize():
        raise SystemExit("no completed post-freeze UTC day is available yet")

    # Fetch far enough back to capture a long native bar that opened before the
    # freeze but only became closed-bar available afterward.
    max_tf_days = max(TFSEC.values()) // 86400
    fetch_start = FROZEN_FORWARD_BOUNDARY.date() - timedelta(days=max_tf_days)
    availability_cutoff = pd.Timestamp(end_day, tz="UTC") + pd.Timedelta(days=1)

    manifest = []
    audits = []
    for interval, seconds in TFSEC.items():
        frames = []
        for day in day_iter(fetch_start, end_day):
            ds = day.isoformat()
            name = f"{args.symbol}-{interval}-{ds}.zip"
            url = f"{DAILY}/{args.symbol}/{interval}/{name}"
            try:
                frame, digest = verified_archive(url)
            except urllib.error.HTTPError as exc:
                if exc.code == 404:
                    manifest.append({
                        "source": "daily",
                        "symbol": args.symbol,
                        "interval": interval,
                        "period": ds,
                        "url": url,
                        "sha256": None,
                        "rows": 0,
                        "status": "404_NO_BAR_OPEN_ON_DAY",
                    })
                    continue
                raise
            frames.append(frame)
            manifest.append({
                "source": "daily",
                "symbol": args.symbol,
                "interval": interval,
                "period": ds,
                "url": url,
                "sha256": digest,
                "rows": len(frame),
                "status": "OK",
            })

        if not frames:
            audits.append({
                "interval": interval,
                "rows": 0,
                "eligible_rows": 0,
                "status": "FAIL_NO_SOURCE_ROWS",
            })
            continue

        frame = pd.concat(frames, ignore_index=True)
        frame["open_time"] = parse_spot_epoch(frame["open_time_epoch"])
        frame = frame.sort_values("open_time", kind="mergesort").drop_duplicates(
            "open_time", keep="last"
        ).reset_index(drop=True)
        frame["availability_time"] = frame["open_time"] + pd.to_timedelta(seconds, unit="s")

        normalized = frame[[
            "open_time", "availability_time", "open", "high", "low", "close",
            "volume", "number_of_trades",
        ]].copy()

        eligible = normalized[
            (normalized["availability_time"] > FROZEN_FORWARD_BOUNDARY)
            & (normalized["availability_time"] <= availability_cutoff)
        ].copy()

        duplicate_count = int(eligible["open_time"].duplicated().sum())
        monotonic = bool(eligible["open_time"].is_monotonic_increasing)
        envelope = (
            (eligible["high"] < eligible[["open", "close", "low"]].max(axis=1))
            | (eligible["low"] > eligible[["open", "close", "high"]].min(axis=1))
        )
        nonpositive = (eligible[["open", "high", "low", "close"]] <= 0).any(axis=1)
        availability_violation = (
            (eligible["availability_time"] <= FROZEN_FORWARD_BOUNDARY)
            | (eligible["availability_time"] > availability_cutoff)
        )

        path = data_dir / f"{args.symbol}_{interval}_forward.csv.gz"
        eligible.to_csv(path, index=False, compression="gzip")
        normalized_hash = sha256_bytes(path.read_bytes())

        failed = (
            len(eligible) == 0
            or duplicate_count != 0
            or not monotonic
            or int(envelope.sum()) != 0
            or int(nonpositive.sum()) != 0
            or int(availability_violation.sum()) != 0
        )
        audits.append({
            "interval": interval,
            "rows": len(normalized),
            "eligible_rows": len(eligible),
            "eligible_start_open": str(eligible["open_time"].iloc[0]) if len(eligible) else None,
            "eligible_end_open": str(eligible["open_time"].iloc[-1]) if len(eligible) else None,
            "eligible_last_availability": str(eligible["availability_time"].iloc[-1]) if len(eligible) else None,
            "duplicate_timestamps": duplicate_count,
            "monotonic": monotonic,
            "ohlc_envelope_failures": int(envelope.sum()),
            "nonpositive_price_rows": int(nonpositive.sum()),
            "availability_out_of_range": int(availability_violation.sum()),
            "normalized_sha256": normalized_hash,
            "status": "FAIL" if failed else "PASS",
        })
        print(interval, len(eligible), flush=True)

    pd.DataFrame(manifest).to_csv(out / "source_manifest.csv", index=False)
    audit = pd.DataFrame(audits)
    audit.to_csv(out / "integrity.csv", index=False)
    failed_series = audit[audit["status"] != "PASS"] if len(audit) else audit

    summary = {
        "status": "PASS" if len(audit) == len(INTERVALS) and failed_series.empty else "FAIL",
        "classification": "POST_FREEZE_NATIVE_DATA_INTAKE_DATA_ONLY",
        "symbol": args.symbol,
        "freeze_boundary_utc_exclusive": FROZEN_FORWARD_BOUNDARY.isoformat(),
        "fetch_start_utc_date": fetch_start.isoformat(),
        "completed_source_day_end_utc": end_day.isoformat(),
        "availability_cutoff_utc_inclusive": availability_cutoff.isoformat(),
        "eligibility_rule": "availability_time > freeze boundary and <= run cutoff",
        "performance_evaluation_allowed": False,
        "candidate_b_judgement_allowed": False,
        "intervals": INTERVALS,
        "failed_series": int(len(failed_series)),
        "timestamp_unit_rule": "Binance Spot archive epoch magnitude: milliseconds below 1e14, microseconds at/above 1e14",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (out / "DATA_GATE.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    if summary["status"] != "PASS":
        raise SystemExit("post-freeze native data integrity gate failed")


if __name__ == "__main__":
    main()

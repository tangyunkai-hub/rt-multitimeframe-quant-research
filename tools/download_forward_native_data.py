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
from typing import Callable, Mapping

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
DENSE_DAILY_ARCHIVE_INTERVALS = {
    interval for interval, seconds in TFSEC.items() if seconds <= 86400
}
MICROSECOND_EPOCH_THRESHOLD = 10**14
FROZEN_FORWARD_BOUNDARY = pd.Timestamp("2026-09-12T02:00:00Z")
MAX_NATIVE_BAR_DAYS = max(TFSEC.values()) // 86400
MONITOR_LOOKBACK_DAYS = MAX_NATIVE_BAR_DAYS + 1
ALLOWED_NONFAIL_GATE_STATUSES = {
    "PASS",
    "PASS_WITH_EXPECTED_EARLY_WAITING_INTERVALS",
    "WAITING_NO_COMPLETED_POST_FREEZE_UTC_DAY",
    "WAITING_SOURCE_ARCHIVE_PUBLICATION",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "rtquant-forward-data/2.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()


def checksum(text: str) -> str:
    lines = text.strip().splitlines()
    if not lines:
        raise ValueError("empty checksum response")
    return lines[0].replace("*", " ").split()[0].lower()


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


def resolve_fetch_start(mode: str, end_day: date) -> date:
    if mode not in {"monitor", "full"}:
        raise ValueError(f"unsupported mode: {mode}")
    full_start = FROZEN_FORWARD_BOUNDARY.date() - timedelta(days=MAX_NATIVE_BAR_DAYS)
    if mode == "full":
        return full_start
    return max(full_start, end_day - timedelta(days=MONITOR_LOOKBACK_DAYS))


def classify_404(interval: str, source_day: date, end_day: date) -> str:
    if interval not in DENSE_DAILY_ARCHIVE_INTERVALS:
        return "404_SPARSE_INTERVAL_NO_BAR_OPEN_ON_DAY"
    if source_day == end_day:
        return "WAITING_SOURCE_ARCHIVE_PUBLICATION"
    return "FAIL_MISSING_EXPECTED_DENSE_ARCHIVE"


def _data_scope(mode: str) -> str:
    if mode == "full":
        return "FULL_REBUILD_COMPLETE_FORWARD_POOL"
    return "MONITOR_BOUNDED_OVERLAP_NOT_COMPLETE_FORWARD_POOL"


def write_waiting_summary(out: Path, symbol: str, end_day: date, mode: str) -> dict:
    summary = {
        "status": "WAITING_NO_COMPLETED_POST_FREEZE_UTC_DAY",
        "classification": "POST_FREEZE_NATIVE_DATA_INTAKE_DATA_ONLY",
        "mode": mode,
        "data_scope": _data_scope(mode),
        "symbol": symbol,
        "freeze_boundary_utc_exclusive": FROZEN_FORWARD_BOUNDARY.isoformat(),
        "completed_source_day_end_utc": end_day.isoformat(),
        "performance_evaluation_allowed": False,
        "candidate_b_judgement_allowed": False,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "DATA_GATE.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    return summary


def derive_overall_status(
    *,
    complete_shape: bool,
    hard_failed_series: int,
    hard_source_gaps: int,
    end_day_publication_missing_intervals: list[str],
    waiting_series: list[str],
) -> str:
    if not complete_shape or hard_failed_series or hard_source_gaps:
        return "FAIL"
    if end_day_publication_missing_intervals:
        return "WAITING_SOURCE_ARCHIVE_PUBLICATION"
    if waiting_series:
        return "PASS_WITH_EXPECTED_EARLY_WAITING_INTERVALS"
    return "PASS"


def collect_forward_data(
    *,
    out: Path,
    symbol: str,
    end_day: date,
    mode: str,
    archive_loader: Callable[[str], tuple[pd.DataFrame, str]] = verified_archive,
    tfsec: Mapping[str, int] = TFSEC,
) -> dict:
    out = Path(out)
    data_dir = out / "binance"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Preserve the preregistered operational rule: do not start the forward pool
    # until there is a fully completed UTC calendar day after the freeze date.
    if pd.Timestamp(end_day, tz="UTC") <= FROZEN_FORWARD_BOUNDARY.normalize():
        return write_waiting_summary(out, symbol, end_day, mode)

    fetch_start = resolve_fetch_start(mode, end_day)
    availability_cutoff = pd.Timestamp(end_day, tz="UTC") + pd.Timedelta(days=1)

    manifest = []
    audits = []
    end_day_publication_missing: set[str] = set()
    hard_source_gaps = []

    for interval, seconds in tfsec.items():
        frames = []
        for source_day in day_iter(fetch_start, end_day):
            ds = source_day.isoformat()
            name = f"{symbol}-{interval}-{ds}.zip"
            url = f"{DAILY}/{symbol}/{interval}/{name}"
            try:
                frame, digest = archive_loader(url)
            except urllib.error.HTTPError as exc:
                if exc.code != 404:
                    raise
                missing_status = classify_404(interval, source_day, end_day)
                record = {
                    "source": "daily",
                    "symbol": symbol,
                    "interval": interval,
                    "period": ds,
                    "url": url,
                    "sha256": None,
                    "rows": 0,
                    "status": missing_status,
                }
                manifest.append(record)
                if missing_status == "WAITING_SOURCE_ARCHIVE_PUBLICATION":
                    end_day_publication_missing.add(interval)
                elif missing_status == "FAIL_MISSING_EXPECTED_DENSE_ARCHIVE":
                    hard_source_gaps.append(record)
                continue

            frames.append(frame)
            manifest.append({
                "source": "daily",
                "symbol": symbol,
                "interval": interval,
                "period": ds,
                "url": url,
                "sha256": digest,
                "rows": len(frame),
                "status": "OK",
            })

        if not frames:
            if interval in end_day_publication_missing:
                status = "WAITING_SOURCE_ARCHIVE_PUBLICATION"
            elif interval in DENSE_DAILY_ARCHIVE_INTERVALS:
                status = "FAIL_NO_SOURCE_ROWS"
            else:
                status = "WAITING_FIRST_COMPLETED_NATIVE_BAR"
            audits.append({
                "interval": interval,
                "rows": 0,
                "eligible_rows": 0,
                "status": status,
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

        path = data_dir / f"{symbol}_{interval}_forward.csv.gz"
        eligible.to_csv(path, index=False, compression="gzip")
        normalized_hash = sha256_bytes(path.read_bytes())

        hard_failure = (
            duplicate_count != 0
            or not monotonic
            or int(envelope.sum()) != 0
            or int(nonpositive.sum()) != 0
            or int(availability_violation.sum()) != 0
        )
        if hard_failure:
            status = "FAIL"
        elif interval in end_day_publication_missing:
            # Never allow yesterday's stale rows to make today's monitor look green.
            status = "WAITING_SOURCE_ARCHIVE_PUBLICATION"
        elif len(eligible) == 0:
            status = "WAITING_FIRST_COMPLETED_NATIVE_BAR"
        else:
            status = "PASS"

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
            "status": status,
        })
        print(interval, len(eligible), status, flush=True)

    pd.DataFrame(manifest).to_csv(out / "source_manifest.csv", index=False)
    audit = pd.DataFrame(audits)
    audit.to_csv(out / "integrity.csv", index=False)

    if len(audit):
        hard_failed = audit[audit["status"].str.startswith("FAIL")]
        waiting = audit[audit["status"].str.startswith("WAITING")]
    else:
        hard_failed = audit
        waiting = audit

    waiting_series = waiting["interval"].tolist() if len(waiting) else []
    missing_latest = sorted(end_day_publication_missing)
    complete_shape = len(audit) == len(tfsec)
    overall_status = derive_overall_status(
        complete_shape=complete_shape,
        hard_failed_series=int(len(hard_failed)),
        hard_source_gaps=len(hard_source_gaps),
        end_day_publication_missing_intervals=missing_latest,
        waiting_series=waiting_series,
    )

    summary = {
        "status": overall_status,
        "classification": "POST_FREEZE_NATIVE_DATA_INTAKE_DATA_ONLY",
        "mode": mode,
        "data_scope": _data_scope(mode),
        "symbol": symbol,
        "freeze_boundary_utc_exclusive": FROZEN_FORWARD_BOUNDARY.isoformat(),
        "fetch_start_utc_date": fetch_start.isoformat(),
        "completed_source_day_end_utc": end_day.isoformat(),
        "availability_cutoff_utc_inclusive": availability_cutoff.isoformat(),
        "eligibility_rule": "availability_time > freeze boundary and <= run cutoff",
        "performance_evaluation_allowed": False,
        "candidate_b_judgement_allowed": False,
        "intervals": list(tfsec),
        "hard_failed_series": int(len(hard_failed)),
        "hard_source_gap_count": len(hard_source_gaps),
        "source_publication_complete_for_end_day": not bool(missing_latest),
        "source_publication_missing_intervals": missing_latest,
        "waiting_series": waiting_series,
        "monitor_lookback_days": MONITOR_LOOKBACK_DAYS if mode == "monitor" else None,
        "timestamp_unit_rule": "Binance Spot archive epoch magnitude: milliseconds below 1e14, microseconds at/above 1e14",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (out / "DATA_GATE.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)

    if overall_status == "FAIL":
        raise SystemExit("post-freeze native data integrity gate failed")
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="forward_native_data")
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument(
        "--end-date",
        default=None,
        help="inclusive UTC YYYY-MM-DD; defaults to yesterday",
    )
    parser.add_argument(
        "--mode",
        choices=("monitor", "full"),
        default="monitor",
        help=(
            "monitor = bounded overlap for scheduled health checks; "
            "full = complete frozen-forward rebuild for audit"
        ),
    )
    args = parser.parse_args()

    end_day = date.fromisoformat(args.end_date) if args.end_date else default_end_date()
    collect_forward_data(
        out=Path(args.out),
        symbol=args.symbol,
        end_day=end_day,
        mode=args.mode,
    )


if __name__ == "__main__":
    main()

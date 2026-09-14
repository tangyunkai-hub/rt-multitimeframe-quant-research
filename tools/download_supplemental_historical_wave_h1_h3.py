from __future__ import annotations

import csv, hashlib, io, json, re, time, urllib.parse, urllib.request, zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

BINANCE_BASE = "https://data.binance.vision/data/spot/monthly/klines"
BITFINEX_BASE = "https://api-pub.bitfinex.com/v2/candles"
KRAKEN_DRIVE_ID = "1ptNqWYidLkhb2VAKuLCxmp2OXEfGO-AP"
H1_START = pd.Timestamp("2023-01-01T00:00:00Z")
H1_END = pd.Timestamp("2026-09-01T00:00:00Z")
PRE_BINANCE_END = pd.Timestamp("2017-08-17T00:00:00Z")
STEP = pd.Timedelta(minutes=15)


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def get(url: str, retries: int = 5) -> bytes:
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "rtquant-supplemental-history/1.0"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read()
        except Exception as e:
            last = e
            time.sleep(min(2 ** i, 10))
    raise RuntimeError(f"download failed {url}: {last}")


def parse_epoch(x: pd.Series) -> pd.DatetimeIndex:
    vals = pd.to_numeric(x, errors="raise").astype("int64")
    med = int(vals.abs().median()) if len(vals) else 0
    if med >= 10**14:
        unit = "us"
    elif med >= 10**11:
        unit = "ms"
    else:
        unit = "s"
    return pd.to_datetime(vals, unit=unit, utc=True)


def audit(df: pd.DataFrame, source: str, instrument: str) -> dict:
    t = pd.to_datetime(df["open_time"], utc=True)
    diffs = t.diff().dropna()
    gaps = diffs[diffs != STEP]
    env = (
        (df["high"] < df[["open", "close", "low"]].max(axis=1)) |
        (df["low"] > df[["open", "close", "high"]].min(axis=1))
    )
    return {
        "source": source,
        "instrument": instrument,
        "rows": int(len(df)),
        "start": str(t.iloc[0]) if len(t) else None,
        "end": str(t.iloc[-1]) if len(t) else None,
        "duplicates": int(t.duplicated().sum()),
        "monotonic": bool(t.is_monotonic_increasing),
        "ohlc_envelope_failures": int(env.sum()),
        "gap_events": int(len(gaps)),
        "missing_15m_intervals_estimate": int(sum(max(int(d / STEP) - 1, 0) for d in gaps)),
        "max_gap_seconds": float(gaps.max().total_seconds()) if len(gaps) else 0.0,
    }


def save_normalized(df: pd.DataFrame, out: Path, rel: str) -> tuple[str, dict]:
    p = out / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    df = df.copy()
    df["open_time"] = pd.to_datetime(df["open_time"], utc=True)
    df["availability_time"] = df["open_time"] + STEP
    cols = ["open_time", "availability_time", "open", "high", "low", "close", "volume"]
    if "number_of_trades" in df.columns:
        cols.append("number_of_trades")
    df[cols].to_csv(p, index=False, compression="gzip")
    return str(p.relative_to(out)), {"normalized_sha256": sha256_bytes(p.read_bytes()), "rows": int(len(df))}


def h1_binance_eth(out: Path) -> tuple[list[dict], list[dict]]:
    symbol, interval = "ETHUSDT", "15m"
    frames, manifest = [], []
    for y in range(2023, 2027):
        for m in range(1, 13):
            month_start = pd.Timestamp(year=y, month=m, day=1, tz="UTC")
            if month_start < H1_START or month_start >= H1_END:
                continue
            ym = f"{y:04d}-{m:02d}"
            name = f"{symbol}-{interval}-{ym}.zip"
            url = f"{BINANCE_BASE}/{symbol}/{interval}/{name}"
            blob = get(url)
            checksum_text = get(url + ".CHECKSUM").decode("utf-8", "replace").strip().splitlines()[0]
            remote_sha = checksum_text.replace("*", " ").split()[0].lower()
            local_sha = sha256_bytes(blob)
            if local_sha != remote_sha:
                raise RuntimeError(f"Binance checksum mismatch {name}")
            with zipfile.ZipFile(io.BytesIO(blob)) as z:
                names = [n for n in z.namelist() if n.lower().endswith(".csv")]
                if len(names) != 1:
                    raise RuntimeError(f"unexpected Binance zip members: {names}")
                d = pd.read_csv(io.BytesIO(z.read(names[0])), header=None)
            if d.shape[1] != 12:
                raise RuntimeError(f"unexpected Binance columns {d.shape[1]} in {name}")
            d.columns = ["open_time_raw","open","high","low","close","volume","close_time_raw","quote_volume","number_of_trades","taker_base","taker_quote","ignore"]
            t = parse_epoch(d["open_time_raw"])
            frame = pd.DataFrame({
                "open_time": t,
                "open": pd.to_numeric(d["open"], errors="raise"),
                "high": pd.to_numeric(d["high"], errors="raise"),
                "low": pd.to_numeric(d["low"], errors="raise"),
                "close": pd.to_numeric(d["close"], errors="raise"),
                "volume": pd.to_numeric(d["volume"], errors="raise"),
                "number_of_trades": pd.to_numeric(d["number_of_trades"], errors="raise").astype("int64"),
            })
            frames.append(frame)
            manifest.append({"wave":"H1","source":"Binance","instrument":symbol,"month":ym,"url":url,"checksum_url":url+".CHECKSUM","zip_sha256":local_sha,"rows":int(len(frame))})
    full = pd.concat(frames, ignore_index=True).sort_values("open_time").drop_duplicates("open_time", keep="last")
    full = full[(full.open_time >= H1_START) & (full.open_time < H1_END)].reset_index(drop=True)
    rel, meta = save_normalized(full, out, "H1_binance/ETHUSDT_15m_2023-01-01_2026-08-31.csv.gz")
    au = audit(full, "Binance", "ETHUSDT")
    au.update(meta); au["normalized_file"] = rel; au["wave"] = "H1"
    return manifest, [au]


def bitfinex_symbol(symbol: str, out: Path) -> tuple[list[dict], dict]:
    start_ms = 0
    end_ms = int((PRE_BINANCE_END - pd.Timedelta(milliseconds=1)).timestamp() * 1000)
    rows: dict[int, list] = {}
    manifest = []
    cursor = start_ms
    while cursor <= end_ms:
        q = urllib.parse.urlencode({"start": cursor, "end": end_ms, "limit": 10000, "sort": 1})
        url = f"{BITFINEX_BASE}/trade:15m:{symbol}/hist?{q}"
        blob = get(url)
        batch = json.loads(blob.decode("utf-8"))
        manifest.append({"wave":"H2","source":"Bitfinex","instrument":symbol,"url":url,"payload_sha256":sha256_bytes(blob),"rows":len(batch)})
        if not batch:
            break
        for r in batch:
            rows[int(r[0])] = r
        last = max(int(r[0]) for r in batch)
        if last >= end_ms or len(batch) < 10000:
            break
        nxt = last + 1
        if nxt <= cursor:
            raise RuntimeError(f"Bitfinex pagination stalled {symbol}")
        cursor = nxt
        time.sleep(0.25)
    if not rows:
        raise RuntimeError(f"no Bitfinex data {symbol}")
    recs = []
    for mts in sorted(rows):
        r = rows[mts]
        recs.append({"open_time": pd.to_datetime(mts, unit="ms", utc=True), "open": float(r[1]), "close": float(r[2]), "high": float(r[3]), "low": float(r[4]), "volume": float(r[5])})
    df = pd.DataFrame(recs)
    df = df[df.open_time < PRE_BINANCE_END].reset_index(drop=True)
    rel, meta = save_normalized(df, out, f"H2_bitfinex/{symbol}_15m_pre_2017-08-17.csv.gz")
    au = audit(df, "Bitfinex", symbol); au.update(meta); au["normalized_file"] = rel; au["wave"] = "H2"
    return manifest, au


def h2_bitfinex(out: Path) -> tuple[list[dict], list[dict]]:
    mans, audits = [], []
    for symbol in ["tBTCUSD", "tETHUSD"]:
        m, a = bitfinex_symbol(symbol, out); mans.extend(m); audits.append(a)
    return mans, audits


def read_kraken_csv(z: zipfile.ZipFile, member: str) -> pd.DataFrame:
    raw = z.read(member)
    d = pd.read_csv(io.BytesIO(raw), header=None)
    if d.shape[1] < 7:
        raise RuntimeError(f"unexpected Kraken columns {d.shape[1]} in {member}")
    # Kraken OHLCVT CSV: time, open, high, low, close, volume, trades
    if not pd.api.types.is_numeric_dtype(d.iloc[:,0]):
        d = pd.read_csv(io.BytesIO(raw))
        vals = d.iloc[:, :7]
    else:
        vals = d.iloc[:, :7]
    vals.columns = ["time_raw","open","high","low","close","volume","number_of_trades"]
    return pd.DataFrame({
        "open_time": parse_epoch(vals["time_raw"]),
        "open": pd.to_numeric(vals["open"], errors="raise"),
        "high": pd.to_numeric(vals["high"], errors="raise"),
        "low": pd.to_numeric(vals["low"], errors="raise"),
        "close": pd.to_numeric(vals["close"], errors="raise"),
        "volume": pd.to_numeric(vals["volume"], errors="raise"),
        "number_of_trades": pd.to_numeric(vals["number_of_trades"], errors="raise").astype("int64"),
    })


def h3_kraken(out: Path) -> tuple[list[dict], list[dict]]:
    import gdown
    zp = out / "kraken_official" / "Kraken_OHLCVT.zip"
    zp.parent.mkdir(parents=True, exist_ok=True)
    ok = gdown.download(id=KRAKEN_DRIVE_ID, output=str(zp), quiet=False)
    if not ok or not zp.exists():
        raise RuntimeError("Kraken official OHLCVT download failed")
    zip_sha = sha256_bytes(zp.read_bytes())
    audits, manifest = [], []
    with zipfile.ZipFile(zp) as z:
        names = z.namelist()
        candidates = {"BTCUSD": [], "ETHUSD": []}
        for n in names:
            base = Path(n).name.upper()
            if re.fullmatch(r"(?:XBT|BTC)USD_15\.CSV", base): candidates["BTCUSD"].append(n)
            if re.fullmatch(r"ETHUSD_15\.CSV", base): candidates["ETHUSD"].append(n)
        for label, members in candidates.items():
            if len(members) != 1:
                raise RuntimeError(f"Kraken expected one {label} 15m member, got {members}")
            member = members[0]
            df = read_kraken_csv(z, member)
            df = df[df.open_time < PRE_BINANCE_END].sort_values("open_time").drop_duplicates("open_time", keep="last").reset_index(drop=True)
            rel, meta = save_normalized(df, out, f"H3_kraken/{label}_15m_pre_2017-08-17.csv.gz")
            au = audit(df, "Kraken", label); au.update(meta); au["normalized_file"] = rel; au["wave"] = "H3"
            audits.append(au)
            manifest.append({"wave":"H3","source":"Kraken","instrument":label,"official_drive_id":KRAKEN_DRIVE_ID,"archive_sha256":zip_sha,"zip_member":member,"member_sha256":sha256_bytes(z.read(member)),"rows_before_endpoint":int(len(df))})
    # The full official archive is not needed in the uploaded artifact after member hashes are frozen.
    zp.unlink()
    return manifest, audits


def main():
    out = Path("supplemental_history_wave_h1_h3")
    out.mkdir(parents=True, exist_ok=True)
    manifest, audits = [], []
    for fn in [h1_binance_eth, h2_bitfinex, h3_kraken]:
        m, a = fn(out); manifest.extend(m); audits.extend(a)
    pd.DataFrame(manifest).to_csv(out / "source_request_manifest.csv", index=False)
    adf = pd.DataFrame(audits)
    adf.to_csv(out / "source_integrity_audit.csv", index=False)
    hard = adf[(adf.rows <= 0) | (adf.duplicates != 0) | (~adf.monotonic) | (adf.ohlc_envelope_failures != 0)]
    endpoint_bad = []
    for _, r in adf.iterrows():
        if r["wave"] == "H1" and pd.Timestamp(r["end"]) >= H1_END:
            endpoint_bad.append(r["instrument"])
        if r["wave"] in ("H2", "H3") and pd.Timestamp(r["end"]) >= PRE_BINANCE_END:
            endpoint_bad.append(r["instrument"])
    status = "PASS" if hard.empty and not endpoint_bad else "FAIL"
    gate = {
        "status": status,
        "classification": "SUPPLEMENTAL_RETROSPECTIVE_SOURCE_GATE__NOT_PROSPECTIVE",
        "waves": ["H1","H2","H3"],
        "series_count": int(len(adf)),
        "hard_failure_count": int(len(hard) + len(endpoint_bad)),
        "endpoint_failures": endpoint_bad,
        "gap_policy": "PRESERVE_SOURCE_GAPS_NO_SYNTHETIC_FILL",
        "strategy_performance_read_allowed": status == "PASS",
        "prospective_evidence_eligible": False,
        "validated_alpha": "NO",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (out / "SOURCE_GATE.json").write_text(json.dumps(gate, indent=2), encoding="utf-8")
    print(json.dumps(gate, indent=2))
    print(adf.to_string(index=False))
    if status != "PASS":
        raise SystemExit("supplemental historical source gate failed")


if __name__ == "__main__":
    main()

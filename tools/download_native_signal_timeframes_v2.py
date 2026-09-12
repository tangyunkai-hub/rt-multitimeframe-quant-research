from __future__ import annotations

import argparse, json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

import download_external_history as base

# Native signal clocks used by the research engine. 15m/2h/8h/3d are already
# present in the run3 artifact; the remaining clocks are added here.
TF_SECONDS = {
    '15m': 900,
    '30m': 1800,
    '1h': 3600,
    '2h': 7200,
    '4h': 14400,
    '8h': 28800,
    '12h': 43200,
    '1d': 86400,
    '3d': 259200,
    '1w': 604800,
}
ADD_INTERVALS = ['30m', '1h', '4h', '12h', '1d', '1w']
REQUIRED_INTERVALS = list(TF_SECONDS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='external_history_2017_2022')
    ap.add_argument('--start-year', type=int, default=2017)
    ap.add_argument('--end-year', type=int, default=2022)
    args = ap.parse_args()
    root = Path(args.root)
    root.mkdir(parents=True, exist_ok=True)
    expected_start = pd.Timestamp(f'{args.start_year}-01-01', tz='UTC')
    expected_end_exclusive = pd.Timestamp(f'{args.end_year + 1}-01-01', tz='UTC')

    # Reuse the checksum-verifying Binance downloader, extending only its
    # duration table. This does not alter the failed v1 historical record.
    base.TFSEC.update(TF_SECONDS)

    manifest = []
    new_audits = []
    for symbol in ['BTCUSDT', 'ETHUSDT']:
        for interval in ADD_INTERVALS:
            print('[native-v2]', symbol, interval, flush=True)
            _, rows, audit = base.binance(
                symbol, interval, args.start_year, args.end_year, root
            )
            manifest.extend(rows)
            new_audits.append(audit)

    pd.DataFrame(manifest).to_csv(
        root / 'binance_native_signal_source_manifest_v2.csv', index=False
    )
    pd.DataFrame(new_audits).to_csv(
        root / 'binance_native_signal_integrity_v2.csv', index=False
    )

    # Independently verify that every required native file exists and passes
    # structural integrity. Cross-granularity equality is intentionally not a
    # hard gate in v2; the source archives are independently authoritative.
    audits = []
    for symbol in ['BTCUSDT', 'ETHUSDT']:
        for interval in REQUIRED_INTERVALS:
            p = root / 'binance' / f'{symbol}_{interval}_{args.start_year}-{args.end_year}.csv.gz'
            if not p.exists():
                audits.append({
                    'symbol': symbol, 'interval': interval, 'exists': False,
                    'rows': 0, 'duplicate_timestamps': None, 'monotonic': None,
                    'ohlc_envelope_failures': None, 'timestamp_out_of_range': None,
                })
                continue
            d = pd.read_csv(p)
            # old archives contain mixed ISO timestamp precision after some
            # maintenance restarts; parse each ISO value robustly.
            t = pd.to_datetime(d['open_time'], utc=True, format='mixed')
            env = (
                (d.high < d[['open', 'close', 'low']].max(axis=1)) |
                (d.low > d[['open', 'close', 'high']].min(axis=1))
            )
            out_of_range = (t < expected_start) | (t >= expected_end_exclusive)
            audits.append({
                'symbol': symbol,
                'interval': interval,
                'exists': True,
                'rows': int(len(d)),
                'start': str(t.iloc[0]) if len(t) else None,
                'end': str(t.iloc[-1]) if len(t) else None,
                'duplicate_timestamps': int(t.duplicated().sum()),
                'monotonic': bool(t.is_monotonic_increasing),
                'ohlc_envelope_failures': int(env.sum()),
                'timestamp_out_of_range': int(out_of_range.sum()),
                'sha256': base.sha(p.read_bytes()),
            })

    audit_df = pd.DataFrame(audits)
    audit_df.to_csv(root / 'NATIVE_TF_V2_INTEGRITY.csv', index=False)
    bad = audit_df[
        (~audit_df.exists.fillna(False)) |
        (audit_df.duplicate_timestamps.fillna(1).astype(int) != 0) |
        (~audit_df.monotonic.fillna(False)) |
        (audit_df.ohlc_envelope_failures.fillna(1).astype(int) != 0) |
        (audit_df.timestamp_out_of_range.fillna(1).astype(int) != 0)
    ]
    summary = {
        'status': 'PASS' if bad.empty else 'FAIL',
        'classification': 'EXTERNAL_HISTORICAL_VALIDATION_NOT_PROSPECTIVE',
        'adapter': 'NATIVE_TIMEFRAME_V2',
        'symbols': ['BTCUSDT', 'ETHUSDT'],
        'native_intervals': REQUIRED_INTERVALS,
        'failed_native_series': int(len(bad)),
        'strategy_evaluation_eligible': False,
        'next_gate': 'MODERN_SAMPLE_NATIVE_ADAPTER_REGRESSION',
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'anti_overfit_rule': 'No strategy semantic, threshold, cost, or sizing change is permitted from external historical performance.',
        'note': 'The failed v1 cross-granularity exact-reconstruction gate remains preserved; v2 uses each official native timeframe independently. Plausible source-period bounds are a hard integrity check.',
    }
    (root / 'NATIVE_TF_V2_DATA_GATE.json').write_text(
        json.dumps(summary, indent=2), encoding='utf-8'
    )
    print(json.dumps(summary, indent=2), flush=True)
    if not bad.empty:
        print(bad.to_string(index=False), flush=True)
        raise SystemExit('native-timeframe v2 integrity gate failed')


if __name__ == '__main__':
    main()

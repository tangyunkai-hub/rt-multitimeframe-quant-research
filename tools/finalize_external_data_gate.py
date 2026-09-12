from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='external_history_2017_2022')
    a = ap.parse_args()
    root = Path(a.root)

    audit_path = root / 'CANONICAL_CHAIN_AUDIT.json'
    if not audit_path.exists():
        raise SystemExit('missing CANONICAL_CHAIN_AUDIT.json; run audit_canonical_external_chain.py first')
    canonical = json.loads(audit_path.read_text())

    parity_path = root / 'binance_native_parity.csv'
    native_groups = 0
    native_mismatch_bars = 0
    if parity_path.exists():
        parity = pd.read_csv(parity_path)
        mm = pd.to_numeric(parity.get('mismatch_bars'), errors='coerce').fillna(0)
        native_groups = int(mm.gt(0).sum())
        native_mismatch_bars = int(mm.sum())

    rec_status = 'NOT_RUN'
    rec_path = root / 'ONE_MINUTE_RECONCILIATION.json'
    if rec_path.exists():
        rec_status = json.loads(rec_path.read_text()).get('status', 'UNKNOWN')

    eligible = canonical.get('status') == 'PASS' and int(canonical.get('hard_source_integrity_failures', 1)) == 0
    summary = {
        'status': 'PASS' if eligible else 'FAIL',
        'classification': 'EXTERNAL_HISTORICAL_VALIDATION_NOT_PROSPECTIVE',
        'data_method_version': 'CANONICAL_15M_AMENDMENT_2026-09-12',
        'hard_source_integrity_failures': int(canonical.get('hard_source_integrity_failures', 0)),
        'canonical_chain_audit_status': canonical.get('status', 'UNKNOWN'),
        'native_higher_tf_parity_role': 'DIAGNOSTIC_ONLY',
        'native_parity_mismatch_groups': native_groups,
        'native_parity_mismatch_bars': native_mismatch_bars,
        'official_1m_forensic_reconciliation_status': rec_status,
        'strategy_evaluation_eligible': bool(eligible),
        'rule': (
            'Checksum-verified Binance 15m is the canonical execution/feature chain. '
            'All Binance-derived strategy candles are built causally from observed canonical 15m bars. '
            'Exchange-maintenance cadence gaps are logged and never filled but do not by themselves invalidate '
            'the containing aggregate. Candles containing off-grid 15m restart bars are quarantined before '
            'indicator computation. Native Binance higher-timeframe parity is diagnostic because official old-history '
            'products were shown to disagree across intervals. No interpolation or synthetic prices are permitted.'
        ),
        'amendment': 'research/external_validation_data_method_amendment_2026-09-12.md',
    }
    (root / 'FINAL_DATA_GATE.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    if not eligible:
        raise SystemExit('external historical data gate failed')


if __name__ == '__main__':
    main()

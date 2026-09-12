from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd


def truthy(v):
    if isinstance(v,bool): return v
    return str(v).strip().lower() in {'true','1','yes'}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='external_history_2017_2022'); a=ap.parse_args(); root=Path(a.root)
    integrity=pd.read_csv(root/'data_integrity_audit.csv')
    hard_integrity=[]
    for _,r in integrity.iterrows():
        if int(r.get('duplicate_timestamps',0))>0 or not truthy(r.get('monotonic',True)) or int(r.get('ohlc_envelope_failures',0))>0:
            hard_integrity.append(r.to_dict())
    parity=pd.read_csv(root/'binance_native_parity.csv')
    mism=parity[pd.to_numeric(parity.mismatch_bars,errors='coerce').fillna(0).gt(0)]
    rec_status='NOT_NEEDED'
    rec_ok=False
    rec_file=root/'ONE_MINUTE_RECONCILIATION.json'
    if len(mism):
        if rec_file.exists():
            rec=json.loads(rec_file.read_text()); rec_status=rec.get('status','UNKNOWN'); rec_ok=rec_status=='PASS'
        else: rec_status='MISSING'
    else: rec_ok=True
    eligible=(len(hard_integrity)==0 and rec_ok)
    summary={
        'status':'PASS' if eligible else 'FAIL',
        'classification':'EXTERNAL_HISTORICAL_VALIDATION_NOT_PROSPECTIVE',
        'hard_integrity_failures':len(hard_integrity),
        'raw_native_parity_mismatch_groups':int(len(mism)),
        'official_1m_reconciliation_status':rec_status,
        'strategy_evaluation_eligible':bool(eligible),
        'rule':'A raw native-parity mismatch is eligible only if official Binance 1m reconstruction resolves every mismatching bin exactly. No interpolation or synthetic price repair is allowed.'
    }
    (root/'FINAL_DATA_GATE.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))
    if not eligible: raise SystemExit('external historical data gate failed')

if __name__=='__main__': main()

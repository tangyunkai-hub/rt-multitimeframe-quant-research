from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

from .prospective import run_prospective_intake


def build_parser() -> argparse.ArgumentParser:
    parser=argparse.ArgumentParser(prog="rtquant-prospective-intake",description=(
        "Run the fail-closed prospective intake chain: full Binance + Bitstamp state-only collection -> "
        "frozen private producer + frozen consumed warmup seed -> provenance contract. No performance is read."))
    parser.add_argument("--repo-root",default=".")
    parser.add_argument("--runtime-dir",default="runtime/prospective")
    parser.add_argument("--end-date",default=None,help="inclusive UTC YYYY-MM-DD")
    parser.add_argument("--private-producer",default=None,help="path to exact frozen private producer bytes")
    parser.add_argument("--warmup-seed",default=None,help="path to exact frozen consumed pre-freeze warmup seed directory")
    parser.add_argument("--warmup-contract",default=None,help="path to exact frozen WARMUP_SEED_CONTRACT.json")
    return parser


def main(argv: Iterable[str] | None=None)->int:
    args=build_parser().parse_args(list(argv) if argv is not None else None)
    try:
        payload=run_prospective_intake(repo_root=Path(args.repo_root),runtime_dir=Path(args.runtime_dir),end_date=args.end_date,
                                       private_producer=args.private_producer,warmup_seed=args.warmup_seed,warmup_contract=args.warmup_contract)
    except Exception as exc:
        payload={"status":"ERROR","performance":None,"performance_embargo_active":True,"candidate_b_judgement_allowed":False,
                 "broker_route":False,"error_type":type(exc).__name__,"message":str(exc)}
        print(json.dumps(payload,indent=2,sort_keys=True)); return 2
    print(json.dumps(payload,indent=2,sort_keys=True,default=str)); return 0

if __name__=="__main__": raise SystemExit(main())

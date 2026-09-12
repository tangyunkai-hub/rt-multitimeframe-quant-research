from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import pandas as pd

from .prospective import prospective_release_gate


CLASSIFICATION = "CANDIDATE_B_PROSPECTIVE_INFORMATION_GATE_ONLY"


def load_forward_states(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".jsonl", ".ndjson"}:
        return pd.read_json(path, lines=True)
    raise ValueError("prospective state input must be .csv, .jsonl, or .ndjson")


def gate_payload(frame: pd.DataFrame) -> dict:
    gate = prospective_release_gate(frame)
    if gate.get("performance") is not None:
        raise RuntimeError("public prospective gate must never release performance")
    return {
        "classification": CLASSIFICATION,
        **gate,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rtquant-prospective-gate",
        description=(
            "Evaluate only the frozen Candidate B prospective information floor. "
            "Thresholds are intentionally not configurable here, and performance "
            "remains embargoed until the separately frozen private evaluator is authorized."
        ),
    )
    parser.add_argument("--input", required=True, help="forward state ledger (.csv/.jsonl/.ndjson)")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        payload = gate_payload(load_forward_states(args.input))
    except Exception as exc:
        print(json.dumps({
            "status": "ERROR",
            "classification": CLASSIFICATION,
            "performance": None,
            "error_type": type(exc).__name__,
            "message": str(exc),
        }, sort_keys=True, indent=2))
        return 2

    print(json.dumps(payload, sort_keys=True, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

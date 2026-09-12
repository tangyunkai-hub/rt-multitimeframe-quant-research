from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import pandas as pd

from rtquant.repro.prospective_contract import (
    read_contract,
    verify_prospective_contract,
)
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


def verified_gate_payload(
    *,
    input_path: str | Path,
    manifest_path: str | Path,
    source_manifest_path: str | Path,
    data_gate_path: str | Path,
) -> dict:
    manifest = read_contract(manifest_path)
    verify_prospective_contract(
        manifest,
        artifact_path=input_path,
        source_manifest_path=source_manifest_path,
        data_gate_path=data_gate_path,
        expected_artifact_kind="candidate_ab_forward_states",
    )
    payload = gate_payload(load_forward_states(input_path))
    payload["provenance"] = {
        "status": "VERIFIED",
        "contract_schema": manifest["schema"],
        "manifest_sha256": manifest["manifest_sha256"],
        "source_snapshot_id": manifest["source"]["snapshot_id"],
    }
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rtquant-prospective-gate",
        description=(
            "Evaluate only the frozen Candidate B prospective information floor. "
            "Operational use is fail-closed: the state ledger must first verify "
            "against its frozen prospective provenance contract. Thresholds are "
            "not configurable, and performance remains embargoed."
        ),
    )
    parser.add_argument("--input", required=True, help="contract-bound forward state ledger CSV")
    parser.add_argument("--manifest", required=True, help="prospective artifact contract JSON")
    parser.add_argument("--source-manifest", required=True, help="exact source_manifest.csv bound by the contract")
    parser.add_argument("--data-gate", required=True, help="exact DATA_GATE.json bound by the contract")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        payload = verified_gate_payload(
            input_path=args.input,
            manifest_path=args.manifest,
            source_manifest_path=args.source_manifest,
            data_gate_path=args.data_gate,
        )
    except Exception as exc:
        print(json.dumps({
            "status": "ERROR",
            "classification": CLASSIFICATION,
            "performance": None,
            "provenance_verified": False,
            "error_type": type(exc).__name__,
            "message": str(exc),
        }, sort_keys=True, indent=2))
        return 2

    print(json.dumps(payload, sort_keys=True, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

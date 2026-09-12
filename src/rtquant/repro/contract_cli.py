from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

from .prospective_contract import (
    build_prospective_contract,
    read_contract,
    verify_prospective_contract,
    write_contract,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rtquant-prospective-contract",
        description="Build or verify a frozen prospective artifact provenance contract.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build")
    build.add_argument("--artifact", required=True)
    build.add_argument(
        "--kind",
        required=True,
        choices=("candidate_ab_forward_states", "candidate_b_paper_bars"),
    )
    build.add_argument("--source-manifest", required=True)
    build.add_argument("--data-gate", required=True)
    build.add_argument("--source-snapshot-id", required=True)
    build.add_argument("--producer-name", required=True)
    build.add_argument("--producer-version", required=True)
    build.add_argument("--producer-code-sha256", required=True)
    build.add_argument("--parent-manifest-sha256")
    build.add_argument("--out", required=True)

    verify = sub.add_parser("verify")
    verify.add_argument("--manifest", required=True)
    verify.add_argument("--artifact", required=True)
    verify.add_argument("--source-manifest", required=True)
    verify.add_argument("--data-gate", required=True)
    verify.add_argument("--expected-kind", choices=("candidate_ab_forward_states", "candidate_b_paper_bars"))
    verify.add_argument("--expected-parent-manifest-sha256")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    try:
        if args.command == "build":
            manifest = build_prospective_contract(
                artifact_path=args.artifact,
                artifact_kind=args.kind,
                source_manifest_path=args.source_manifest,
                data_gate_path=args.data_gate,
                source_snapshot_id=args.source_snapshot_id,
                producer_name=args.producer_name,
                producer_version=args.producer_version,
                producer_code_sha256=args.producer_code_sha256,
                parent_manifest_sha256=args.parent_manifest_sha256,
            )
            write_contract(manifest, args.out)
            result = {
                "status": "PASS",
                "manifest": str(Path(args.out)),
                "manifest_sha256": manifest["manifest_sha256"],
                "artifact_kind": manifest["artifact_kind"],
                "performance_embargo_active": True,
            }
        else:
            manifest = read_contract(args.manifest)
            verify_prospective_contract(
                manifest,
                artifact_path=args.artifact,
                source_manifest_path=args.source_manifest,
                data_gate_path=args.data_gate,
                expected_artifact_kind=args.expected_kind,
                expected_parent_manifest_sha256=args.expected_parent_manifest_sha256,
            )
            result = {
                "status": "PASS",
                "manifest_sha256": manifest["manifest_sha256"],
                "artifact_kind": manifest["artifact_kind"],
                "performance_embargo_active": True,
            }
    except Exception as exc:
        print(json.dumps({
            "status": "FAIL",
            "error_type": type(exc).__name__,
            "message": str(exc),
            "performance_embargo_active": True,
        }, indent=2, sort_keys=True))
        return 2

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

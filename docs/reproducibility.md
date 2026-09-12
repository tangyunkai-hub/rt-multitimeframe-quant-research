# Reproducibility

## Environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest -q
```

CI runs the public test suite on Python 3.10, 3.11, and 3.12.

## Run provenance

Each research run should record:

- input file SHA-256 hashes;
- code file hashes or the frozen commit identifier;
- protocol/version identifier;
- timestamp range;
- evidence classification and status;
- invariant results;
- output manifest hash.

A changed strategy-defining file requires a new version. Reusing the same filename is not sufficient provenance.

## Manifest rules

`rtquant.repro.build_manifest()` hashes the exact input bytes. The manifest layer is deliberately fail-closed:

- duplicate basename keys are rejected instead of silently overwriting one another;
- when files from multiple directories are expected, pass an explicit `root=` so stable relative paths become manifest keys;
- `verify_manifest()` recomputes the manifest self-hash and every declared file hash;
- changing an input byte or changing manifest metadata invalidates verification.

Example:

```python
from rtquant.repro import build_manifest, verify_manifest

manifest = build_manifest(
    run_id="example-run",
    files=["data/input.csv", "results/summary.json"],
    root=".",
    metadata={"evidence_class": "SYNTHETIC_DEMO"},
)
verify_manifest(
    manifest,
    files=["data/input.csv", "results/summary.json"],
    root=".",
)
```

## Paper-shadow audit chain

The brokerless paper layer stores an append-only JSONL journal. Each processed bar records the canonical bar payload, execution-cost assumptions, state-before hash, complete recovered state, state-after hash, and a record hash chained to the previous record.

A restart does not trust a serialized final state blindly: `replay_journal()` verifies the chain and replays every bar through the deterministic paper engine. Changed data at an already processed timestamp requires a versioned replay; it cannot silently overwrite history.

## Synthetic demo

```bash
python examples/run_synthetic_demo.py
```

The demo is intentionally synthetic. It verifies architecture and causal behavior only; it is not evidence of Alpha.

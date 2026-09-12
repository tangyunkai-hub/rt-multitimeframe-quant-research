# Reproducibility

## Environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest -q
```

## Run provenance

Each research run should record:

- input file SHA-256 hashes;
- code file hashes;
- protocol/version identifier;
- timestamp range;
- evidence status;
- invariant results;
- output manifest hash.

A changed strategy-defining file requires a new version. Reusing the same filename is not sufficient provenance.

## Synthetic demo

```bash
python examples/run_synthetic_demo.py
```

The demo is intentionally synthetic. It verifies architecture and causal behavior only.

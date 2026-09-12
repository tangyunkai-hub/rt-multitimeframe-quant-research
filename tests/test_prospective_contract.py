import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from rtquant.repro.prospective_contract import (
    FROZEN_PROTOCOL_COMMITMENTS,
    ProspectiveContractError,
    build_prospective_contract,
    verify_prospective_contract,
)


PRODUCER_SHA = "a" * 64


def _source_files(tmp_path: Path, *, mode="full", status="PASS"):
    source_manifest = tmp_path / "source_manifest.csv"
    source_manifest.write_text("source,sha256\ndaily,abc\n", encoding="utf-8")
    data_gate = tmp_path / "DATA_GATE.json"
    scope = (
        "FULL_REBUILD_COMPLETE_FORWARD_POOL"
        if mode == "full"
        else "MONITOR_BOUNDED_OVERLAP_NOT_COMPLETE_FORWARD_POOL"
    )
    data_gate.write_text(json.dumps({
        "status": status,
        "mode": mode,
        "data_scope": scope,
        "freeze_boundary_utc_exclusive": "2026-09-12T02:00:00+00:00",
        "completed_source_day_end_utc": "2026-09-20",
        "performance_evaluation_allowed": False,
        "candidate_b_judgement_allowed": False,
    }), encoding="utf-8")
    return source_manifest, data_gate


def _states(path: Path):
    pd.DataFrame([
        {"timestamp": "2026-09-13T04:00:00Z", "A_core": "CORE_SHORT", "B_core": "FLAT", "major_bear_epoch_id": "bear-1"},
        {"timestamp": "2026-09-13T06:00:00Z", "A_core": "FLAT", "B_core": "FLAT", "major_bear_epoch_id": "bear-1"},
    ]).to_csv(path, index=False)


def _paper(path: Path):
    pd.DataFrame([
        {"timestamp": "2026-09-13T04:00:00Z", "open": 100.0, "close": 101.0, "target_exposure": 0.0},
        {"timestamp": "2026-09-13T06:00:00Z", "open": 101.0, "close": 102.0, "target_exposure": -1.0},
    ]).to_csv(path, index=False)


def _build(tmp_path: Path, artifact: Path, kind: str, *, mode="full", parent=None):
    source_manifest, data_gate = _source_files(tmp_path, mode=mode)
    manifest = build_prospective_contract(
        artifact_path=artifact,
        artifact_kind=kind,
        source_manifest_path=source_manifest,
        data_gate_path=data_gate,
        source_snapshot_id="forward-run-001",
        producer_name="private-frozen-engine",
        producer_version="v0.24",
        producer_code_sha256=PRODUCER_SHA,
        parent_manifest_sha256=parent,
    )
    return manifest, source_manifest, data_gate


def test_frozen_commitments_are_exact_sha256_digests():
    assert len(FROZEN_PROTOCOL_COMMITMENTS) == 6
    for digest in FROZEN_PROTOCOL_COMMITMENTS.values():
        assert len(digest) == 64
        int(digest, 16)


def test_state_ledger_contract_roundtrip(tmp_path):
    artifact = tmp_path / "states.csv"
    _states(artifact)
    manifest, source_manifest, data_gate = _build(
        tmp_path, artifact, "candidate_ab_forward_states"
    )
    assert manifest["performance_embargo_active"] is True
    assert manifest["artifact"]["rows"] == 2
    assert manifest["frozen_protocol_commitments"] == FROZEN_PROTOCOL_COMMITMENTS
    assert verify_prospective_contract(
        manifest,
        artifact_path=artifact,
        source_manifest_path=source_manifest,
        data_gate_path=data_gate,
        expected_artifact_kind="candidate_ab_forward_states",
    )


def test_state_ledger_requires_full_source_snapshot(tmp_path):
    artifact = tmp_path / "states.csv"
    _states(artifact)
    with pytest.raises(ProspectiveContractError, match="mode=full"):
        _build(tmp_path, artifact, "candidate_ab_forward_states", mode="monitor")


def test_paper_bars_may_bind_to_monitor_snapshot_and_parent(tmp_path):
    artifact = tmp_path / "paper.csv"
    _paper(artifact)
    parent = "b" * 64
    manifest, source_manifest, data_gate = _build(
        tmp_path, artifact, "candidate_b_paper_bars", mode="monitor", parent=parent
    )
    assert verify_prospective_contract(
        manifest,
        artifact_path=artifact,
        source_manifest_path=source_manifest,
        data_gate_path=data_gate,
        expected_artifact_kind="candidate_b_paper_bars",
        expected_parent_manifest_sha256=parent,
    )


def test_artifact_byte_change_fails_verification(tmp_path):
    artifact = tmp_path / "states.csv"
    _states(artifact)
    manifest, source_manifest, data_gate = _build(
        tmp_path, artifact, "candidate_ab_forward_states"
    )
    artifact.write_text(artifact.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ProspectiveContractError, match="SHA-256 mismatch"):
        verify_prospective_contract(
            manifest,
            artifact_path=artifact,
            source_manifest_path=source_manifest,
            data_gate_path=data_gate,
        )


def test_source_gate_byte_change_fails_verification(tmp_path):
    artifact = tmp_path / "states.csv"
    _states(artifact)
    manifest, source_manifest, data_gate = _build(
        tmp_path, artifact, "candidate_ab_forward_states"
    )
    gate = json.loads(data_gate.read_text(encoding="utf-8"))
    gate["completed_source_day_end_utc"] = "2026-09-21"
    data_gate.write_text(json.dumps(gate), encoding="utf-8")
    with pytest.raises(ProspectiveContractError, match="DATA_GATE SHA-256 mismatch"):
        verify_prospective_contract(
            manifest,
            artifact_path=artifact,
            source_manifest_path=source_manifest,
            data_gate_path=data_gate,
        )


def test_protocol_commitment_substitution_fails_even_with_rehashed_manifest(tmp_path):
    artifact = tmp_path / "states.csv"
    _states(artifact)
    manifest, source_manifest, data_gate = _build(
        tmp_path, artifact, "candidate_ab_forward_states"
    )
    manifest["frozen_protocol_commitments"]["candidate_b_engine"] = "0" * 64
    unsigned = {k: v for k, v in manifest.items() if k != "manifest_sha256"}
    canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")
    manifest["manifest_sha256"] = hashlib.sha256(canonical).hexdigest()
    with pytest.raises(ProspectiveContractError, match="frozen protocol commitment mismatch"):
        verify_prospective_contract(
            manifest,
            artifact_path=artifact,
            source_manifest_path=source_manifest,
            data_gate_path=data_gate,
        )


def test_performance_columns_are_rejected_before_contract_creation(tmp_path):
    artifact = tmp_path / "states.csv"
    pd.DataFrame([{
        "timestamp": "2026-09-13T04:00:00Z",
        "A_core": "CORE_SHORT",
        "B_core": "FLAT",
        "major_bear_epoch_id": "bear-1",
        "candidate_b_return": 0.03,
    }]).to_csv(artifact, index=False)
    with pytest.raises(ProspectiveContractError, match="performance-like columns"):
        _build(tmp_path, artifact, "candidate_ab_forward_states")


def test_waiting_source_gate_cannot_produce_operational_artifact(tmp_path):
    artifact = tmp_path / "paper.csv"
    _paper(artifact)
    source_manifest, data_gate = _source_files(
        tmp_path, mode="monitor", status="WAITING_SOURCE_ARCHIVE_PUBLICATION"
    )
    with pytest.raises(ProspectiveContractError, match="not eligible"):
        build_prospective_contract(
            artifact_path=artifact,
            artifact_kind="candidate_b_paper_bars",
            source_manifest_path=source_manifest,
            data_gate_path=data_gate,
            source_snapshot_id="forward-run-waiting",
            producer_name="private-frozen-engine",
            producer_version="v0.24",
            producer_code_sha256=PRODUCER_SHA,
        )

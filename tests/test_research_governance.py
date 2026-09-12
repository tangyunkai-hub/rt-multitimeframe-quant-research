import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_public_manifest_preserves_non_deployment_state():
    manifest = json.loads((ROOT / "PUBLIC_RELEASE_MANIFEST.json").read_text())
    assert manifest["research_status"] == "NOT_DEPLOYMENT_READY"
    assert manifest["holdout_status"] == "FAIL"
    assert manifest["candidate_status"] == "FROZEN_HYPOTHESIS_NOT_VALIDATED"
    assert manifest["prospective_v024_status"] == "INSUFFICIENT_FORWARD_EVIDENCE"
    assert manifest["validated_alpha_established"] is False
    assert manifest["small_capital_live_eligible"] is False


def test_external_history_cannot_masquerade_as_prospective_confirmation():
    manifest = json.loads((ROOT / "PUBLIC_RELEASE_MANIFEST.json").read_text())
    ext = manifest["external_historical_validation"]
    assert ext["classification"] == "EXTERNAL_HISTORICAL_VALIDATION_NOT_PROSPECTIVE"
    assert ext["status"] == "COMPLETE"
    assert ext["btc"] == "ADVERSE_EXTERNAL_MECHANISM_EVIDENCE"
    assert ext["eth"] == "EXTERNAL_MECHANISM_SUPPORT"
    assert ext["cross_asset"] == "HETEROGENEOUS_NO_UNIFORM_REPLICATION"


def test_external_result_document_retains_both_positive_and_negative_evidence():
    text = (ROOT / "research" / "external_validation_results_2017_2022_2026-09-12.md").read_text()
    assert "ADVERSE_EXTERNAL_MECHANISM_EVIDENCE" in text
    assert "EXTERNAL_MECHANISM_SUPPORT" in text
    assert "validated Alpha is not established" in text
    assert "SMALL_CAPITAL_LIVE_ELIGIBLE` is **not** reached" in text

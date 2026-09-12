import pytest

from rtquant.repro import ManifestIntegrityError, build_manifest, verify_manifest


def test_manifest_changes_with_bytes(tmp_path):
    p = tmp_path / "x.txt"
    p.write_text("a")
    a = build_manifest(run_id="x", files=[p])
    p.write_text("b")
    b = build_manifest(run_id="x", files=[p])
    assert a["manifest_sha256"] != b["manifest_sha256"]


def test_duplicate_basename_requires_explicit_root(tmp_path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    a.mkdir()
    b.mkdir()
    pa = a / "summary.json"
    pb = b / "summary.json"
    pa.write_text("a")
    pb.write_text("b")

    with pytest.raises(ValueError, match="duplicate manifest key"):
        build_manifest(run_id="x", files=[pa, pb])

    manifest = build_manifest(run_id="x", files=[pa, pb], root=tmp_path)
    assert set(manifest["files"]) == {"a/summary.json", "b/summary.json"}


def test_verify_manifest_detects_file_mutation(tmp_path):
    p = tmp_path / "x.txt"
    p.write_text("a")
    manifest = build_manifest(run_id="x", files=[p])
    assert verify_manifest(manifest, files=[p]) is True
    p.write_text("changed")
    with pytest.raises(ManifestIntegrityError, match="file hashes"):
        verify_manifest(manifest, files=[p])


def test_verify_manifest_detects_manifest_tampering(tmp_path):
    p = tmp_path / "x.txt"
    p.write_text("a")
    manifest = build_manifest(run_id="x", files=[p], metadata={"candidate": "A"})
    manifest["metadata"]["candidate"] = "B"
    with pytest.raises(ManifestIntegrityError, match="self-hash"):
        verify_manifest(manifest, files=[p])

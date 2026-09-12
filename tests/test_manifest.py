from pathlib import Path
from rtquant.repro import build_manifest

def test_manifest_changes_with_bytes(tmp_path):
    p=tmp_path/'x.txt'; p.write_text('a'); a=build_manifest(run_id='x',files=[p])
    p.write_text('b'); b=build_manifest(run_id='x',files=[p])
    assert a['manifest_sha256']!=b['manifest_sha256']

import importlib.util
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("warmup",ROOT/"tools"/"build_v024_warmup_seed.py")
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)


def test_warmup_audit_rejects_postfreeze_rows():
    d=pd.DataFrame([{"availability_time":mod.FREEZE+pd.Timedelta("15m"),"open":1.0,"high":2.0,"low":1.0,"close":1.5,"volume":1.0}])
    a=mod.audit_frame(d,name="x")
    assert a["status"] == "FAIL"
    assert a["post_freeze_rows"] == 1


def test_warmup_audit_accepts_boundary_row():
    d=pd.DataFrame([{"availability_time":mod.FREEZE,"open":1.0,"high":2.0,"low":1.0,"close":1.5,"volume":1.0}])
    a=mod.audit_frame(d,name="x")
    assert a["status"] == "PASS"
    assert a["post_freeze_rows"] == 0

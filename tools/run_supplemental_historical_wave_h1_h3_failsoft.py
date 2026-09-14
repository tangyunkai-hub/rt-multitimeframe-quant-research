from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import download_supplemental_historical_wave_h1_h3 as src


def main():
    out = Path("supplemental_history_wave_h1_h3")
    out.mkdir(parents=True, exist_ok=True)
    manifest: list[dict] = []
    audits: list[dict] = []
    wave_status: dict[str, dict] = {}

    waves = [
        ("H1", src.h1_binance_eth),
        ("H2", src.h2_bitfinex),
        ("H3", src.h3_kraken),
    ]

    for wave, fn in waves:
        try:
            m, a = fn(out)
            manifest.extend(m)
            for row in a:
                p = out / row["normalized_file"]
                d = pd.read_csv(p, compression="gzip")
                ot = pd.to_datetime(d["open_time"], utc=True, format="mixed")
                av = pd.to_datetime(d["availability_time"], utc=True, format="mixed")
                row["availability_identity_open_plus_15m"] = bool(
                    (av == ot + pd.Timedelta(minutes=15)).all()
                )
                audits.append(row)
            wave_status[wave] = {"status": "ACQUIRED", "error": None}
        except Exception as e:
            wave_status[wave] = {
                "status": "BLOCKED_EXTERNAL_OR_SOURCE_ACQUISITION",
                "error_type": type(e).__name__,
                "error": str(e),
            }

    pd.DataFrame(manifest).to_csv(out / "source_request_manifest.csv", index=False)
    adf = pd.DataFrame(audits)
    adf.to_csv(out / "source_integrity_audit.csv", index=False)

    series_status = []
    for _, r in adf.iterrows():
        hard_ok = (
            int(r["rows"]) > 0
            and int(r["duplicates"]) == 0
            and bool(r["monotonic"])
            and int(r["ohlc_envelope_failures"]) == 0
            and bool(r["availability_identity_open_plus_15m"])
        )
        endpoint_ok = True
        if r["wave"] == "H1":
            endpoint_ok = pd.Timestamp(r["end"]) < src.H1_END
        elif r["wave"] in ("H2", "H3"):
            endpoint_ok = pd.Timestamp(r["end"]) < src.PRE_BINANCE_END
        series_status.append({
            "wave": r["wave"],
            "source": r["source"],
            "instrument": r["instrument"],
            "hard_integrity_pass": bool(hard_ok),
            "endpoint_pass": bool(endpoint_ok),
            "gap_events": int(r["gap_events"]),
            "missing_15m_intervals_estimate": int(r["missing_15m_intervals_estimate"]),
            "normalized_sha256": r["normalized_sha256"],
        })

    sframe = pd.DataFrame(series_status)
    ready = {}
    for wave in ["H1", "H2", "H3"]:
        w = sframe[sframe.wave == wave] if len(sframe) else pd.DataFrame()
        expected_n = {"H1": 1, "H2": 2, "H3": 2}[wave]
        acquired = wave_status.get(wave, {}).get("status") == "ACQUIRED"
        ok = acquired and len(w) == expected_n and bool(w.hard_integrity_pass.all()) and bool(w.endpoint_pass.all())
        ready[wave] = bool(ok)

    if ready["H1"] and ready["H2"] and ready["H3"]:
        overall = "PASS_ALL_WAVES_SOURCE_READY"
    elif ready["H1"] and ready["H2"]:
        overall = "PARTIAL_READY_H1_H2__H3_BLOCKED"
    else:
        overall = "BLOCKED_REQUIRED_READY_WAVE_FAILED"

    gate = {
        "status": overall,
        "classification": "SUPPLEMENTAL_RETROSPECTIVE_SOURCE_GATE__NOT_PROSPECTIVE",
        "wave_status": wave_status,
        "wave_source_ready": ready,
        "series": series_status,
        "gap_policy": "PRESERVE_SOURCE_GAPS_NO_SYNTHETIC_FILL",
        "H1_H2_ready_for_implementation_compatibility": bool(ready["H1"] and ready["H2"]),
        "strategy_performance_read_allowed": False,
        "reason_performance_embargoed": "Compatibility and no-performance event-identity gates must pass and event hashes must be frozen before any supplemental historical outcome read.",
        "prospective_evidence_eligible": False,
        "validated_alpha": "NO",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (out / "SOURCE_GATE.json").write_text(json.dumps(gate, indent=2), encoding="utf-8")
    print(json.dumps(gate, indent=2))
    if len(adf):
        print(adf.to_string(index=False))

    # H3 external-host blocking must not erase successful H1/H2 evidence.
    # Fail only when H1/H2 themselves cannot reach the source-ready boundary.
    if not (ready["H1"] and ready["H2"]):
        raise SystemExit("H1/H2 supplemental historical source gate not ready")


if __name__ == "__main__":
    main()

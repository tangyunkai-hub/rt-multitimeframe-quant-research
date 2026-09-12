from datetime import date
import urllib.error

import pandas as pd

from tools import download_forward_native_data as forward


def _frame_for_day(source_day: date, interval_seconds: int = 900) -> pd.DataFrame:
    open_time = pd.Timestamp(f"{source_day.isoformat()}T12:00:00Z")
    open_ms = int(open_time.value // 1_000_000)
    close_ms = open_ms + interval_seconds * 1000 - 1
    return pd.DataFrame([[
        open_ms,
        100.0,
        102.0,
        99.0,
        101.0,
        10.0,
        close_ms,
        1000.0,
        1,
        5.0,
        500.0,
        0,
    ]], columns=forward.COLS)


def _source_day_from_url(url: str) -> date:
    stem = url.rsplit("/", 1)[-1].removesuffix(".zip")
    return date.fromisoformat(stem[-10:])


def test_monitor_fetch_is_bounded_but_full_rebuild_starts_at_frozen_overlap():
    end_day = date(2026, 9, 30)
    assert forward.resolve_fetch_start("monitor", end_day) == date(2026, 9, 22)
    assert forward.resolve_fetch_start("full", end_day) == date(2026, 9, 5)


def test_404_classification_distinguishes_publication_wait_from_source_gap():
    end_day = date(2026, 9, 30)
    assert (
        forward.classify_404("15m", end_day, end_day)
        == "WAITING_SOURCE_ARCHIVE_PUBLICATION"
    )
    assert (
        forward.classify_404("15m", date(2026, 9, 29), end_day)
        == "FAIL_MISSING_EXPECTED_DENSE_ARCHIVE"
    )
    assert (
        forward.classify_404("1w", end_day, end_day)
        == "404_SPARSE_INTERVAL_NO_BAR_OPEN_ON_DAY"
    )


def test_freeze_day_waits_without_touching_source_and_keeps_performance_embargo(tmp_path):
    def should_not_be_called(_url: str):
        raise AssertionError("source must not be called before a completed post-freeze UTC day")

    summary = forward.collect_forward_data(
        out=tmp_path,
        symbol="BTCUSDT",
        end_day=date(2026, 9, 12),
        mode="monitor",
        archive_loader=should_not_be_called,
        tfsec={"15m": 900},
    )

    assert summary["status"] == "WAITING_NO_COMPLETED_POST_FREEZE_UTC_DAY"
    assert summary["performance_evaluation_allowed"] is False
    assert summary["candidate_b_judgement_allowed"] is False


def test_missing_latest_dense_archive_cannot_be_masked_by_stale_valid_rows(tmp_path):
    end_day = date(2026, 9, 21)

    def loader(url: str):
        source_day = _source_day_from_url(url)
        if source_day == end_day:
            raise urllib.error.HTTPError(url, 404, "not published", hdrs=None, fp=None)
        return _frame_for_day(source_day), f"digest-{source_day.isoformat()}"

    summary = forward.collect_forward_data(
        out=tmp_path,
        symbol="BTCUSDT",
        end_day=end_day,
        mode="monitor",
        archive_loader=loader,
        tfsec={"15m": 900},
    )

    assert summary["status"] == "WAITING_SOURCE_ARCHIVE_PUBLICATION"
    assert summary["source_publication_complete_for_end_day"] is False
    assert summary["source_publication_missing_intervals"] == ["15m"]
    assert summary["hard_source_gap_count"] == 0
    assert summary["performance_evaluation_allowed"] is False
    assert summary["candidate_b_judgement_allowed"] is False

    integrity = pd.read_csv(tmp_path / "integrity.csv")
    assert integrity.loc[0, "eligible_rows"] > 0
    assert integrity.loc[0, "status"] == "WAITING_SOURCE_ARCHIVE_PUBLICATION"


def test_historical_dense_archive_gap_fails_closed(tmp_path):
    end_day = date(2026, 9, 21)
    missing_day = date(2026, 9, 18)

    def loader(url: str):
        source_day = _source_day_from_url(url)
        if source_day == missing_day:
            raise urllib.error.HTTPError(url, 404, "missing", hdrs=None, fp=None)
        return _frame_for_day(source_day), f"digest-{source_day.isoformat()}"

    try:
        forward.collect_forward_data(
            out=tmp_path,
            symbol="BTCUSDT",
            end_day=end_day,
            mode="monitor",
            archive_loader=loader,
            tfsec={"15m": 900},
        )
    except SystemExit as exc:
        assert "integrity gate failed" in str(exc)
    else:
        raise AssertionError("historical dense archive gap must fail closed")

    gate = pd.read_json(tmp_path / "DATA_GATE.json", typ="series")
    assert gate["status"] == "FAIL"
    assert gate["hard_source_gap_count"] == 1


def test_publication_wait_precedes_ordinary_waiting_in_overall_status():
    status = forward.derive_overall_status(
        complete_shape=True,
        hard_failed_series=0,
        hard_source_gaps=0,
        end_day_publication_missing_intervals=["15m"],
        waiting_series=["1w"],
    )
    assert status == "WAITING_SOURCE_ARCHIVE_PUBLICATION"

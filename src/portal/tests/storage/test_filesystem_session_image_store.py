import os
from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from chromasense.core.models import EnhancementResult, Outcome, PairOutcome, SessionImage
from chromasense.storage.filesystem_session_image_store import FilesystemSessionImageStore
from color_engine.models import CvdProfile, CvdType, Palette2

SESSION = "session-abcdefghijklmnop"
OTHER = "other-session-0123456789"
NOW = datetime(2026, 11, 19, 12, 0, tzinfo=UTC)


@pytest.fixture
def store(tmp_path):
    return FilesystemSessionImageStore(tmp_path)


def _image(image_id="image-1", seed=0):
    pixels = np.random.default_rng(seed).integers(0, 256, size=(30, 40, 3), dtype=np.uint8)
    return SessionImage(
        image_id=image_id,
        pixels=pixels,
        width=40,
        height=30,
        source_format="JPEG",
        uploaded_at=NOW,
    )


def _result(image_id="image-1", enhanced=True):
    rng = np.random.default_rng(1)
    palette = Palette2(
        colors_rgb=np.array([[200, 40, 40], [40, 160, 40]], dtype=np.uint8),
        colors_lab=np.array([[44.0, 60.0, 40.0], [57.0, -55.0, 50.0]]),
        labels=rng.integers(0, 2, size=(30, 40), dtype=np.int32),
        counts=np.array([600, 600], dtype=np.int64),
    )
    return EnhancementResult(
        image_id=image_id,
        profile=CvdProfile(CvdType.PROTAN, 0.75),
        outcome=Outcome.ENHANCED if enhanced else Outcome.NO_CONFUSABLE_PAIRS,
        message="Adjusted 1 of 1 color pairs likely to be confused.",
        palette=palette,
        mask=rng.integers(0, 2, size=(30, 40)).astype(bool),
        enhanced_pixels=rng.integers(0, 256, size=(30, 40, 3), dtype=np.uint8)
        if enhanced
        else None,
        pairs=(PairOutcome("#c82828", "#28a028", 7.0, 13.6, True),) if enhanced else (),
        eligible_count=1 if enhanced else 0,
        improved_count=1 if enhanced else 0,
        newly_confusable_count=0,
    )


def _files(tmp_path):
    return sorted(str(path.relative_to(tmp_path)) for path in tmp_path.rglob("*") if path.is_file())


def test_original_round_trip(store):
    image = _image()
    store.save_original(SESSION, image)
    loaded = store.load_original(SESSION)
    np.testing.assert_array_equal(loaded.pixels, image.pixels)
    assert loaded.pixels.dtype == np.uint8
    assert (loaded.image_id, loaded.width, loaded.height) == ("image-1", 40, 30)
    assert loaded.source_format == "JPEG"
    assert loaded.uploaded_at == NOW


@pytest.mark.parametrize("enhanced", [True, False])
def test_result_round_trip(store, enhanced):
    store.save_original(SESSION, _image())
    result = _result(enhanced=enhanced)
    store.save_result(SESSION, result)
    loaded = store.load_result(SESSION)

    assert loaded.image_id == result.image_id
    assert loaded.profile == result.profile
    assert loaded.outcome is result.outcome
    assert loaded.message == result.message
    assert loaded.pairs == result.pairs
    assert (loaded.eligible_count, loaded.improved_count, loaded.newly_confusable_count) == (
        result.eligible_count,
        result.improved_count,
        result.newly_confusable_count,
    )
    for field in ("colors_rgb", "colors_lab", "labels", "counts"):
        np.testing.assert_array_equal(
            getattr(loaded.palette, field), getattr(result.palette, field)
        )
    np.testing.assert_array_equal(loaded.mask, result.mask)
    if enhanced:
        np.testing.assert_array_equal(loaded.enhanced_pixels, result.enhanced_pixels)
    else:
        assert loaded.enhanced_pixels is None


def test_missing_session_loads_nothing(store):
    assert store.load_original(SESSION) is None
    assert store.load_result(SESSION) is None


def test_saving_an_original_removes_the_result_files(store, tmp_path):
    store.save_original(SESSION, _image())
    store.save_result(SESSION, _result())
    store.save_original(SESSION, _image("image-2", seed=5))

    assert store.load_result(SESSION) is None
    assert store.load_original(SESSION).image_id == "image-2"
    names = {path.name for path in (tmp_path / "sessions" / SESSION).iterdir()}
    assert names == {"original.npy", "original.json"}


def test_result_without_enhanced_pixels_removes_an_older_enhanced_file(store, tmp_path):
    store.save_original(SESSION, _image())
    store.save_result(SESSION, _result(enhanced=True))
    store.save_result(SESSION, _result(enhanced=False))
    assert not (tmp_path / "sessions" / SESSION / "enhanced.npy").exists()
    assert store.load_result(SESSION).enhanced_pixels is None


def test_delete_session_leaves_nothing_for_it(store, tmp_path):
    for session in (SESSION, OTHER):
        store.save_original(session, _image())
        store.save_result(session, _result())
        store.touch(session, NOW)

    store.delete_session(SESSION)

    assert not (tmp_path / "sessions" / SESSION).exists()
    assert not any(SESSION in name for name in _files(tmp_path))
    assert store.load_original(OTHER) is not None


def test_deleting_a_missing_session_is_allowed(store):
    store.delete_session(SESSION)


def test_idle_sessions_use_the_last_touch(store):
    store.touch(SESSION, NOW - timedelta(minutes=31))
    store.touch(OTHER, NOW - timedelta(minutes=5))
    assert store.idle_sessions(NOW - timedelta(minutes=30)) == [SESSION]
    assert store.idle_sessions(NOW + timedelta(days=1)) == sorted([SESSION, OTHER])


def test_touch_marks_the_session_as_used(store):
    store.touch(SESSION, NOW - timedelta(minutes=31))
    store.touch(SESSION, NOW)
    assert store.idle_sessions(NOW - timedelta(minutes=30)) == []


def test_files_stay_inside_the_session_folder_and_no_temporary_files_remain(store, tmp_path):
    store.save_original(SESSION, _image())
    store.save_result(SESSION, _result())
    store.touch(SESSION, NOW)
    files = _files(tmp_path)
    assert all(name.startswith(os.path.join("sessions", SESSION) + os.sep) for name in files)
    assert not any(".tmp-" in name for name in files)
    assert {os.path.basename(name) for name in files} == {
        "original.npy",
        "original.json",
        "result.json",
        "result.npz",
        "enhanced.npy",
        "last_used",
    }


def test_failed_write_leaves_no_partial_file(store, tmp_path, monkeypatch):
    store.save_original(SESSION, _image())

    def broken_save(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(np, "save", broken_save)
    with pytest.raises(OSError):
        store.save_original(SESSION, _image("image-2"))
    monkeypatch.undo()

    assert not any(".tmp-" in name for name in _files(tmp_path))


@pytest.mark.parametrize(
    "session_id",
    ["../x", "abc", "a" * 129, "session/with/slash-0000", "session id with spaces", ""],
)
def test_session_ids_that_could_form_a_path_are_rejected(store, session_id):
    for call in (
        lambda: store.load_original(session_id),
        lambda: store.save_original(session_id, _image()),
        lambda: store.touch(session_id, NOW),
        lambda: store.delete_session(session_id),
    ):
        with pytest.raises(ValueError):
            call()


def test_unrelated_folders_are_never_listed_as_sessions(store, tmp_path):
    (tmp_path / "sessions" / "not a session").mkdir()
    store.touch(SESSION, NOW - timedelta(hours=1))
    assert store.idle_sessions(NOW) == [SESSION]


def test_real_store_with_purge_and_end_session_leaves_no_files(store, tmp_path):
    from chromasense.core.use_cases.end_session import EndSession, EndSessionRequest
    from chromasense.core.use_cases.purge_idle_sessions import (
        PurgeIdleSessions,
        PurgeIdleSessionsRequest,
    )

    class Clock:
        def now(self):
            return NOW

    for session in (SESSION, OTHER):
        store.save_original(session, _image())
        store.save_result(session, _result())
    store.touch(SESSION, NOW - timedelta(minutes=31))
    store.touch(OTHER, NOW - timedelta(minutes=5))

    deleted = PurgeIdleSessions(store, Clock(), idle_minutes=30).execute(PurgeIdleSessionsRequest())
    assert deleted.deleted == 1
    assert not any(SESSION in name for name in _files(tmp_path))

    EndSession(store).execute(EndSessionRequest(session_id=OTHER))
    assert _files(tmp_path) == []

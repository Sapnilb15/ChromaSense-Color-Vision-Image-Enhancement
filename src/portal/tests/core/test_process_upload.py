import re

import pytest

from chromasense.core.errors import UploadRejected
from chromasense.core.models import ProcessingSettings, UploadRejection
from chromasense.core.use_cases.process_upload import (
    REJECTION_MESSAGES,
    ProcessUpload,
    ProcessUploadRequest,
)

SESSION = "session-abcdefghijklmnop"


def _upload(store, clock, data, session=SESSION):
    use_case = ProcessUpload(store, clock, ProcessingSettings())
    return use_case.execute(ProcessUploadRequest(session_id=session, data=data))


@pytest.mark.parametrize(("name", "image_format"), [("valid.png", "PNG"), ("valid.jpg", "JPEG")])
def test_valid_png_and_jpeg_are_stored(store, clock, sample, name, image_format):
    response = _upload(store, clock, sample(name))

    assert (response.width, response.height) == (60, 40)
    stored = store.load_original(SESSION)
    assert stored.image_id == response.image_id
    assert stored.pixels.shape == (40, 60, 3)
    assert stored.source_format == image_format
    assert stored.uploaded_at == clock.now()
    assert store.touched[SESSION] == clock.now()


def test_image_ids_are_new_random_hex(store, clock, sample):
    first = _upload(store, clock, sample("valid.png")).image_id
    second = _upload(store, clock, sample("valid.png")).image_id
    assert re.fullmatch(r"[0-9a-f]{32}", first)
    assert first != second


@pytest.mark.parametrize(
    ("name", "reason"),
    [
        ("not_an_image.png", UploadRejection.UNSUPPORTED_TYPE),
        ("truncated.jpg", UploadRejection.CORRUPT),
        ("over_12mp.png", UploadRejection.TOO_MANY_PIXELS),
    ],
)
def test_invalid_files_are_rejected_with_reason_and_message(store, clock, sample, name, reason):
    with pytest.raises(UploadRejected) as caught:
        _upload(store, clock, sample(name))

    assert caught.value.reason is reason
    assert caught.value.message == REJECTION_MESSAGES[reason]
    assert store.originals == {}
    assert store.calls == []
    assert store.touched == {}


def test_file_over_ten_megabytes_is_too_large(store, clock, sample):
    with pytest.raises(UploadRejected) as caught:
        _upload(store, clock, sample("valid.png") + b"\0" * (10 * 1024 * 1024))
    assert caught.value.reason is UploadRejection.TOO_LARGE
    assert caught.value.message == "This file is larger than 10 MB."
    assert store.originals == {}


def test_messages_match_the_increment():
    assert REJECTION_MESSAGES == {
        UploadRejection.UNSUPPORTED_TYPE: "This file is not a PNG or JPEG image.",
        UploadRejection.CORRUPT: "This image file is damaged or incomplete and cannot be opened.",
        UploadRejection.TOO_LARGE: "This file is larger than 10 MB.",
        UploadRejection.TOO_MANY_PIXELS: "This image is larger than 12 megapixels.",
    }


def test_second_upload_replaces_the_first_and_discards_the_result(store, clock, sample):
    first = _upload(store, clock, sample("valid.png"))
    store.save_result(SESSION, "earlier result")

    second = _upload(store, clock, sample("valid.jpg"))

    assert store.load_original(SESSION).image_id == second.image_id != first.image_id
    assert store.load_result(SESSION) is None


def test_rejected_upload_leaves_the_session_unchanged(store, clock, sample):
    kept = _upload(store, clock, sample("valid.png"))
    store.save_result(SESSION, "earlier result")
    clock.advance(5)

    with pytest.raises(UploadRejected):
        _upload(store, clock, sample("truncated.jpg"))

    assert store.load_original(SESSION).image_id == kept.image_id
    assert store.load_result(SESSION) == "earlier result"
    assert store.touched[SESSION] < clock.now()


def test_sessions_are_kept_apart(store, clock, sample):
    _upload(store, clock, sample("valid.png"), session="first-session-0000")
    _upload(store, clock, sample("valid.jpg"), session="second-session-000")
    assert store.load_original("first-session-0000").source_format == "PNG"
    assert store.load_original("second-session-000").source_format == "JPEG"

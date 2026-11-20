"""Use case: decode an uploaded file and store it as the session's original image."""

from dataclasses import dataclass
from uuid import uuid4

from chromasense.core.errors import UploadRejected
from chromasense.core.models import ProcessingSettings, SessionImage, UploadRejection
from chromasense.core.ports import Clock, SessionImageStore
from color_engine.models import DecodeError, DecodeReason
from color_engine.pipeline.filter_1_decode.decode_1 import decode_1

REJECTION_MESSAGES = {
    UploadRejection.UNSUPPORTED_TYPE: "This file is not a PNG or JPEG image.",
    UploadRejection.CORRUPT: "This image file is damaged or incomplete and cannot be opened.",
    UploadRejection.TOO_LARGE: "This file is larger than 10 MB.",
    UploadRejection.TOO_MANY_PIXELS: "This image is larger than 12 megapixels.",
}

_REJECTION_FOR = {
    DecodeReason.UNSUPPORTED_TYPE: UploadRejection.UNSUPPORTED_TYPE,
    DecodeReason.CORRUPT: UploadRejection.CORRUPT,
    DecodeReason.TOO_LARGE: UploadRejection.TOO_LARGE,
    DecodeReason.TOO_MANY_PIXELS: UploadRejection.TOO_MANY_PIXELS,
}


@dataclass(frozen=True)
class ProcessUploadRequest:
    session_id: str
    data: bytes


@dataclass(frozen=True)
class ProcessUploadResponse:
    image_id: str
    width: int
    height: int


class ProcessUpload:
    def __init__(
        self, store: SessionImageStore, clock: Clock, settings: ProcessingSettings
    ) -> None:
        self._store = store
        self._clock = clock
        self._settings = settings

    def execute(self, request: ProcessUploadRequest) -> ProcessUploadResponse:
        try:
            decoded = decode_1(request.data, self._settings.input_limits)
        except DecodeError as error:
            rejection = _REJECTION_FOR[error.reason]
            raise UploadRejected(rejection, REJECTION_MESSAGES[rejection]) from error

        now = self._clock.now()
        image = SessionImage(
            image_id=uuid4().hex,
            pixels=decoded.pixels,
            width=decoded.width,
            height=decoded.height,
            source_format=decoded.source_format,
            uploaded_at=now,
        )
        self._store.save_original(request.session_id, image)
        self._store.touch(request.session_id, now)
        return ProcessUploadResponse(image.image_id, image.width, image.height)

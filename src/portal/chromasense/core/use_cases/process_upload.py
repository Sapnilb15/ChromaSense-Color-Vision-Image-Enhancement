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
    """The session and the uploaded file's bytes."""

    session_id: str
    data: bytes


@dataclass(frozen=True)
class ProcessUploadResponse:
    """The new image's ID and size."""

    image_id: str
    width: int
    height: int


class ProcessUpload:
    """Decode an upload with filter 1 and store it as the session's original image.

    Args:
        store: The session image store.
        clock: The clock, used for the upload time and the session's last use.
        settings: The input limits.
    """

    def __init__(
        self, store: SessionImageStore, clock: Clock, settings: ProcessingSettings
    ) -> None:
        self._store = store
        self._clock = clock
        self._settings = settings

    def execute(self, request: ProcessUploadRequest) -> ProcessUploadResponse:
        """Validate and decode the upload, replacing the session's image and result.

        Args:
            request: The session and the uploaded bytes.

        Returns:
            The new image's ID, width, and height.

        Raises:
            UploadRejected: If the file is not a PNG or JPEG, is corrupt, is larger than
                10 MB, or is larger than 12 megapixels. The error carries a message for
                the user.
        """
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

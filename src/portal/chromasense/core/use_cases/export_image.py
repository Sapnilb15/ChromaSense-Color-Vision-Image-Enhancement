"""Use case: return the enhanced image as a PNG download at the original resolution."""

from dataclasses import dataclass

from chromasense.core.errors import NoImageInSession
from chromasense.core.ports import Clock, SessionImageStore
from color_engine.rules.encode import encode_png

EXPORT_FILENAME = "chromasense-enhanced.png"


@dataclass(frozen=True)
class ExportImageRequest:
    """Which session's enhanced image to export."""

    session_id: str


@dataclass(frozen=True)
class ExportImageResponse:
    """The enhanced image as PNG bytes, with the download file name."""

    png: bytes
    filename: str


class ExportImage:
    """Export the session's enhanced image as a PNG at the original resolution.

    Args:
        store: The session image store.
        clock: The clock, used to record when the session was last used.
    """

    def __init__(self, store: SessionImageStore, clock: Clock) -> None:
        self._store = store
        self._clock = clock

    def execute(self, request: ExportImageRequest) -> ExportImageResponse:
        """Encode the stored enhanced pixels as a PNG.

        Args:
            request: The session.

        Returns:
            The PNG bytes and the file name ``chromasense-enhanced.png``.

        Raises:
            NoImageInSession: If the session has no result, or its result has no
                enhanced image.
        """
        result = self._store.load_result(request.session_id)
        if result is None or result.enhanced_pixels is None:
            raise NoImageInSession("There is no enhanced image to download.")

        self._store.touch(request.session_id, self._clock.now())
        return ExportImageResponse(png=encode_png(result.enhanced_pixels), filename=EXPORT_FILENAME)

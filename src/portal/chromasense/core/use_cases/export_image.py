"""Use case: return the enhanced image as a PNG download at the original resolution."""

from dataclasses import dataclass

from chromasense.core.errors import NoImageInSession
from chromasense.core.ports import Clock, SessionImageStore
from color_engine.rules.encode import encode_png

EXPORT_FILENAME = "chromasense-enhanced.png"


@dataclass(frozen=True)
class ExportImageRequest:
    session_id: str


@dataclass(frozen=True)
class ExportImageResponse:
    png: bytes
    filename: str


class ExportImage:
    def __init__(self, store: SessionImageStore, clock: Clock) -> None:
        self._store = store
        self._clock = clock

    def execute(self, request: ExportImageRequest) -> ExportImageResponse:
        result = self._store.load_result(request.session_id)
        if result is None or result.enhanced_pixels is None:
            raise NoImageInSession("There is no enhanced image to download.")

        self._store.touch(request.session_id, self._clock.now())
        return ExportImageResponse(png=encode_png(result.enhanced_pixels), filename=EXPORT_FILENAME)

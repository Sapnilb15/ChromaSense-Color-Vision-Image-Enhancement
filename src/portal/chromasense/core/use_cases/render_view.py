"""Use case: return the session's original or enhanced image as PNG bytes for display."""

from dataclasses import dataclass

from chromasense.core.errors import NoImageInSession
from chromasense.core.models import View
from chromasense.core.ports import Clock, SessionImageStore
from color_engine.rules.encode import encode_png


@dataclass(frozen=True)
class RenderViewRequest:
    """The session and which version of its image to render."""

    session_id: str
    view: View


@dataclass(frozen=True)
class RenderViewResponse:
    """The requested version as PNG bytes, with the image's ID."""

    png: bytes
    image_id: str


class RenderView:
    """Return the session's original or enhanced image for display.

    Args:
        store: The session image store.
        clock: The clock, used to record when the session was last used.
    """

    def __init__(self, store: SessionImageStore, clock: Clock) -> None:
        self._store = store
        self._clock = clock

    def execute(self, request: RenderViewRequest) -> RenderViewResponse:
        """Encode the requested version of the session image as a PNG.

        Args:
            request: The session and the view, original or enhanced.

        Returns:
            The PNG bytes and the original image's ID.

        Raises:
            NoImageInSession: If the session has no uploaded image, or the enhanced view
                is requested and there is no enhanced image.
        """
        original = self._store.load_original(request.session_id)
        if original is None:
            raise NoImageInSession("Upload an image first.")

        if request.view is View.ORIGINAL:
            pixels = original.pixels
        else:
            result = self._store.load_result(request.session_id)
            if result is None or result.enhanced_pixels is None:
                raise NoImageInSession("There is no enhanced image yet.")
            pixels = result.enhanced_pixels

        self._store.touch(request.session_id, self._clock.now())
        return RenderViewResponse(png=encode_png(pixels), image_id=original.image_id)

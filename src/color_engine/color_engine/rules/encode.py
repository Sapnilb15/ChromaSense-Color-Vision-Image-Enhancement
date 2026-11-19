"""PNG encoding."""

import io

import numpy as np
from numpy.typing import NDArray
from PIL import Image


def encode_png(pixels: NDArray[np.uint8]) -> bytes:
    """Encode sRGB uint8 pixels of shape (H, W, 3) as PNG bytes."""
    image = np.asarray(pixels)
    if image.dtype != np.uint8 or image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("pixels must be a uint8 array of shape (H, W, 3)")
    buffer = io.BytesIO()
    Image.fromarray(image).save(buffer, format="PNG")
    return buffer.getvalue()

"""PNG encoding."""

import io

import numpy as np
from numpy.typing import NDArray
from PIL import Image


def encode_png(pixels: NDArray[np.uint8]) -> bytes:
    """Encode an sRGB image as a lossless PNG.

    Args:
        pixels: sRGB uint8 array of shape (height, width, 3).

    Returns:
        The PNG file as bytes. Decoding it gives back ``pixels`` exactly.

    Raises:
        ValueError: If ``pixels`` is not a uint8 array of shape (height, width, 3).
    """
    image = np.asarray(pixels)
    if image.dtype != np.uint8 or image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("pixels must be a uint8 array of shape (H, W, 3)")
    buffer = io.BytesIO()
    Image.fromarray(image).save(buffer, format="PNG")
    return buffer.getvalue()

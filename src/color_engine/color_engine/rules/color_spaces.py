"""sRGB transfer function and CIELAB conversion."""

import numpy as np
from numpy.typing import NDArray
from skimage.color import lab2rgb, rgb2lab


def srgb_to_linear(pixels: NDArray) -> NDArray[np.float64]:
    """Linearize sRGB values with the sRGB transfer function.

    Args:
        pixels: sRGB values of any shape, as uint8 from 0 to 255 or floats from 0 to 1.

    Returns:
        Linear RGB values from 0 to 1, as float64 with the same shape.
    """
    values = np.asarray(pixels)
    encoded = values / 255.0 if values.dtype == np.uint8 else values.astype(np.float64)
    return np.where(encoded <= 0.04045, encoded / 12.92, ((encoded + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(pixels: NDArray) -> NDArray[np.float64]:
    """Encode linear RGB values with the sRGB transfer function.

    Args:
        pixels: Linear RGB values of any shape. Values outside 0 to 1 are clipped first.

    Returns:
        sRGB values from 0 to 1, as float64 with the same shape.
    """
    linear = np.clip(np.asarray(pixels, dtype=np.float64), 0.0, 1.0)
    return np.where(linear <= 0.0031308, linear * 12.92, 1.055 * linear ** (1 / 2.4) - 0.055)


def rgb_to_lab(pixels: NDArray[np.uint8]) -> NDArray[np.float64]:
    """Convert sRGB values to CIELAB under the D65 illuminant.

    Args:
        pixels: sRGB uint8 array with R, G, and B on the last axis.

    Returns:
        float64 array of the same shape with L, a, and b on the last axis.
    """
    return rgb2lab(np.asarray(pixels, dtype=np.uint8))


def lab_to_rgb(lab: NDArray) -> NDArray[np.uint8]:
    """Convert CIELAB values under the D65 illuminant to sRGB.

    Args:
        lab: Array with L, a, and b on the last axis.

    Returns:
        uint8 array of the same shape with R, G, and B on the last axis. Out-of-gamut
        values are rounded and clipped to 0 to 255.
    """
    rgb = lab2rgb(np.asarray(lab, dtype=np.float64))
    return np.clip(np.rint(rgb * 255.0), 0, 255).astype(np.uint8)

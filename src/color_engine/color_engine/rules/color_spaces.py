"""sRGB transfer function and CIELAB conversion."""

import numpy as np
from numpy.typing import NDArray
from skimage.color import lab2rgb, rgb2lab


def srgb_to_linear(pixels: NDArray) -> NDArray[np.float64]:
    """Linearize sRGB values from 0 to 1. A uint8 array is first scaled from 0-255 to 0-1."""
    values = np.asarray(pixels)
    encoded = values / 255.0 if values.dtype == np.uint8 else values.astype(np.float64)
    return np.where(encoded <= 0.04045, encoded / 12.92, ((encoded + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(pixels: NDArray) -> NDArray[np.float64]:
    """Encode linear RGB values as sRGB from 0 to 1, clipping them to that range first."""
    linear = np.clip(np.asarray(pixels, dtype=np.float64), 0.0, 1.0)
    return np.where(linear <= 0.0031308, linear * 12.92, 1.055 * linear ** (1 / 2.4) - 0.055)


def rgb_to_lab(pixels: NDArray[np.uint8]) -> NDArray[np.float64]:
    """Convert sRGB uint8 values, with RGB on the last axis, to CIELAB (D65)."""
    return rgb2lab(np.asarray(pixels, dtype=np.uint8))


def lab_to_rgb(lab: NDArray) -> NDArray[np.uint8]:
    """Convert CIELAB (D65) values to sRGB uint8, rounding and clipping out-of-gamut values."""
    rgb = lab2rgb(np.asarray(lab, dtype=np.float64))
    return np.clip(np.rint(rgb * 255.0), 0, 255).astype(np.uint8)

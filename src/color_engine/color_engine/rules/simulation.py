"""Protan and deutan simulation with the Machado (2009) model, applied in linear RGB."""

import json
from functools import cache
from importlib import resources

import numpy as np
from numpy.typing import NDArray

from color_engine.models import CvdProfile, CvdType
from color_engine.rules.color_spaces import linear_to_srgb, srgb_to_linear


def simulate(pixels: NDArray[np.uint8], profile: CvdProfile) -> NDArray[np.uint8]:
    """Simulate how colors appear under a CVD profile, with Machado (2009) in linear RGB.

    Args:
        pixels: sRGB uint8 array with R, G, and B on the last axis.
        profile: The CVD type and severity. Severity 0 returns an unchanged copy.

    Returns:
        Simulated sRGB uint8 array with the same shape as ``pixels``.

    Raises:
        ValueError: If ``pixels`` is not a uint8 array with 3 values on the last axis.
    """
    image = np.asarray(pixels)
    if image.dtype != np.uint8 or image.ndim < 1 or image.shape[-1] != 3:
        raise ValueError("pixels must be a uint8 RGB array")
    if profile.severity == 0.0:
        return image.copy()
    linear = srgb_to_linear(image)
    simulated = linear @ machado_matrix(profile.type, profile.severity).T
    return np.rint(linear_to_srgb(simulated) * 255.0).astype(np.uint8)


def machado_matrix(cvd_type: CvdType, severity: float) -> NDArray[np.float64]:
    """Return the Machado (2009) matrix for a CVD type and severity.

    Args:
        cvd_type: Protan or deutan.
        severity: From 0 to 1. The matrix is interpolated linearly between the two
            nearest 0.1 steps in ``data/machado_2009.json``.

    Returns:
        float64 array of shape (3, 3) that acts on linear RGB column vectors.
    """
    tables = _machado_tables()[cvd_type.value]
    position = severity * (len(tables) - 1)
    lower = min(int(position), len(tables) - 2)
    weight = position - lower
    return (1.0 - weight) * tables[lower] + weight * tables[lower + 1]


@cache
def _machado_tables() -> dict[str, NDArray[np.float64]]:
    source = resources.files("color_engine").joinpath("data/machado_2009.json")
    data = json.loads(source.read_text(encoding="utf-8"))
    return {key: np.array(data[key], dtype=np.float64) for key in ("protan", "deutan")}

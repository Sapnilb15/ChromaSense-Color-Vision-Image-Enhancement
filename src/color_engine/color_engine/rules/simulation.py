"""Protan and deutan simulation with the Machado (2009) model, applied in linear RGB."""

import json
from functools import cache
from importlib import resources

import numpy as np
from numpy.typing import NDArray

from color_engine.models import CvdProfile, CvdType
from color_engine.rules.color_spaces import linear_to_srgb, srgb_to_linear


def simulate(pixels: NDArray[np.uint8], profile: CvdProfile) -> NDArray[np.uint8]:
    """Return how sRGB uint8 pixels, with RGB on the last axis, appear under the profile."""
    image = np.asarray(pixels)
    if image.dtype != np.uint8 or image.ndim < 1 or image.shape[-1] != 3:
        raise ValueError("pixels must be a uint8 RGB array")
    if profile.severity == 0.0:
        return image.copy()
    linear = srgb_to_linear(image)
    simulated = linear @ machado_matrix(profile.type, profile.severity).T
    return np.rint(linear_to_srgb(simulated) * 255.0).astype(np.uint8)


def machado_matrix(cvd_type: CvdType, severity: float) -> NDArray[np.float64]:
    """Return the Machado matrix for the type, interpolated between the two nearest 0.1 steps."""
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

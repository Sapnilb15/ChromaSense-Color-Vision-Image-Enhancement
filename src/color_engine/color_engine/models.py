"""Shared Color Engine models and the numbered filter outputs."""

from dataclasses import dataclass
from enum import Enum

import numpy as np
from numpy.typing import NDArray


class CvdType(Enum):
    PROTAN = "protan"
    DEUTAN = "deutan"


@dataclass(frozen=True)
class CvdProfile:
    type: CvdType
    severity: float

    def __post_init__(self) -> None:
        if not isinstance(self.type, CvdType):
            raise ValueError("type must be a CvdType")
        if not 0.0 <= self.severity <= 1.0:
            raise ValueError("severity must be between 0 and 1")


@dataclass(frozen=True)
class InputLimits:
    max_bytes: int = 10 * 1024 * 1024
    max_megapixels: float = 12.0


class DecodeReason(Enum):
    UNSUPPORTED_TYPE = "unsupported_type"
    CORRUPT = "corrupt"
    TOO_LARGE = "too_large"
    TOO_MANY_PIXELS = "too_many_pixels"


class DecodeError(Exception):
    """Raised by filter 1 when uploaded bytes cannot become an image."""

    def __init__(self, reason: DecodeReason) -> None:
        super().__init__(reason.value)
        self.reason = reason


@dataclass(frozen=True)
class DecodedImage1:
    pixels: NDArray[np.uint8]
    width: int
    height: int
    source_format: str


@dataclass(frozen=True)
class Palette2:
    """Dominant colors, ordered by pixel count, with each pixel's palette index."""

    colors_rgb: NDArray[np.uint8]
    colors_lab: NDArray[np.float64]
    labels: NDArray[np.int32]
    counts: NDArray[np.int64]


@dataclass(frozen=True)
class ConfusablePair:
    a: int
    b: int
    original_distance: float
    simulated_distance: float


@dataclass(frozen=True)
class ConfusionResult3:
    """Palette pairs that become confusable under the profile, their groups, and their pixels."""

    palette: Palette2
    profile: CvdProfile
    threshold: float
    pairs: tuple[ConfusablePair, ...]
    groups: tuple[tuple[int, ...], ...]
    mask: NDArray[np.bool_]


@dataclass(frozen=True)
class EnhancedImage4:
    """Enhanced pixels, each palette color's CIELAB after enhancement, and which colors moved."""

    pixels: NDArray[np.uint8]
    palette_lab_after: NDArray[np.float64]
    changed: NDArray[np.bool_]


@dataclass(frozen=True)
class PairSeparation:
    a: int
    b: int
    before: float
    after: float
    improved: bool


@dataclass(frozen=True)
class SeparationReport5:
    """Simulated separation of each flagged pair before and after enhancement."""

    pairs: tuple[PairSeparation, ...]
    newly_confusable: tuple[tuple[int, int], ...]
    eligible_count: int
    improved_count: int

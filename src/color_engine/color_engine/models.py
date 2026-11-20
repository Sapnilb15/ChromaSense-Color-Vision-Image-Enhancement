"""Shared Color Engine models and the numbered filter outputs."""

from dataclasses import dataclass
from enum import Enum

import numpy as np
from numpy.typing import NDArray


class CvdType(Enum):
    """The red–green color vision deficiency types that ChromaSense supports."""

    PROTAN = "protan"
    DEUTAN = "deutan"


@dataclass(frozen=True)
class CvdProfile:
    """A CVD type and severity, used to simulate how colors appear.

    Attributes:
        type: The deficiency type, protan or deutan.
        severity: From 0 (no deficiency) to 1 (full dichromacy).

    Raises:
        ValueError: If ``type`` is not a ``CvdType`` or ``severity`` is outside 0 to 1.
    """

    type: CvdType
    severity: float

    def __post_init__(self) -> None:
        if not isinstance(self.type, CvdType):
            raise ValueError("type must be a CvdType")
        if not 0.0 <= self.severity <= 1.0:
            raise ValueError("severity must be between 0 and 1")


@dataclass(frozen=True)
class InputLimits:
    """Upload limits that filter 1 enforces before it decodes pixels.

    Attributes:
        max_bytes: Largest accepted file size in bytes. Defaults to 10 MB.
        max_megapixels: Largest accepted width times height, in millions. Defaults to 12.
    """

    max_bytes: int = 10 * 1024 * 1024
    max_megapixels: float = 12.0


class DecodeReason(Enum):
    """Why filter 1 rejected an upload."""

    UNSUPPORTED_TYPE = "unsupported_type"
    CORRUPT = "corrupt"
    TOO_LARGE = "too_large"
    TOO_MANY_PIXELS = "too_many_pixels"


class DecodeError(Exception):
    """Raised by filter 1 when uploaded bytes cannot become an image.

    Args:
        reason: Why the bytes were rejected. Also stored as ``self.reason``.
    """

    def __init__(self, reason: DecodeReason) -> None:
        super().__init__(reason.value)
        self.reason = reason


@dataclass(frozen=True)
class DecodedImage1:
    """Output of filter 1: a validated image as 8-bit sRGB pixels.

    Attributes:
        pixels: sRGB uint8 array of shape (height, width, 3), upright and with any
            transparency placed on white.
        width: Width in pixels.
        height: Height in pixels.
        source_format: The detected file format, ``"PNG"`` or ``"JPEG"``.
    """

    pixels: NDArray[np.uint8]
    width: int
    height: int
    source_format: str


@dataclass(frozen=True)
class Palette2:
    """Output of filter 2: dominant colors, ordered by pixel count, with each pixel's index.

    Attributes:
        colors_rgb: sRGB uint8 array of shape (k, 3).
        colors_lab: CIELAB float64 array of shape (k, 3), matching ``colors_rgb``.
        labels: int32 array of shape (height, width) giving each pixel's palette index.
        counts: int64 array of shape (k,) giving how many pixels each color has.
    """

    colors_rgb: NDArray[np.uint8]
    colors_lab: NDArray[np.float64]
    labels: NDArray[np.int32]
    counts: NDArray[np.int64]


@dataclass(frozen=True)
class ConfusablePair:
    """Two palette colors that are distinct in the original but confusable when simulated.

    Attributes:
        a: Palette index of the first color.
        b: Palette index of the second color, greater than ``a``.
        original_distance: CIEDE2000 distance between the original colors.
        simulated_distance: CIEDE2000 distance between the simulated colors.
    """

    a: int
    b: int
    original_distance: float
    simulated_distance: float


@dataclass(frozen=True)
class ConfusionResult3:
    """Output of filter 3: pairs that become confusable under the profile, and their pixels.

    Attributes:
        palette: The palette that the pairs index into.
        profile: The profile used for simulation.
        threshold: The CIEDE2000 confusion threshold used.
        pairs: Each flagged pair.
        groups: Palette indexes joined by flagged pairs, one tuple for each linked group.
        mask: bool array of shape (height, width), true for pixels of flagged colors.
    """

    palette: Palette2
    profile: CvdProfile
    threshold: float
    pairs: tuple[ConfusablePair, ...]
    groups: tuple[tuple[int, ...], ...]
    mask: NDArray[np.bool_]


@dataclass(frozen=True)
class EnhancedImage4:
    """Output of filter 4: the enhanced image and how each palette color moved.

    Attributes:
        pixels: sRGB uint8 array of shape (height, width, 3). Pixels outside the
            confusion mask equal the original exactly.
        palette_lab_after: CIELAB float64 array of shape (k, 3) after enhancement.
        changed: bool array of shape (k,), true for each palette color that moved.
    """

    pixels: NDArray[np.uint8]
    palette_lab_after: NDArray[np.float64]
    changed: NDArray[np.bool_]


@dataclass(frozen=True)
class PairSeparation:
    """Simulated separation of one flagged pair before and after enhancement.

    Attributes:
        a: Palette index of the first color.
        b: Palette index of the second color.
        before: Simulated CIEDE2000 distance before enhancement.
        after: Simulated CIEDE2000 distance after enhancement.
        improved: True when ``after`` is greater than ``before``.
    """

    a: int
    b: int
    before: float
    after: float
    improved: bool


@dataclass(frozen=True)
class SeparationReport5:
    """Output of filter 5: simulated separation of each flagged pair before and after.

    Attributes:
        pairs: One entry for each flagged pair.
        newly_confusable: Palette index pairs that were not flagged but fall below the
            threshold after enhancement.
        eligible_count: Number of flagged pairs.
        improved_count: Number of flagged pairs whose simulated distance grew.
    """

    pairs: tuple[PairSeparation, ...]
    newly_confusable: tuple[tuple[int, int], ...]
    eligible_count: int
    improved_count: int

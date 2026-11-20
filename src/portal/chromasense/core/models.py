"""Application Core models."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import numpy as np
from numpy.typing import NDArray

from color_engine.models import CvdProfile, InputLimits, Palette2


class UploadRejection(Enum):
    """Why an upload was rejected. Each value has a user-facing message in ``ProcessUpload``."""

    UNSUPPORTED_TYPE = "unsupported_type"
    CORRUPT = "corrupt"
    TOO_LARGE = "too_large"
    TOO_MANY_PIXELS = "too_many_pixels"


@dataclass(frozen=True)
class SessionImage:
    """The session's decoded original image.

    Attributes:
        image_id: A new random ID for each upload, so a result can be matched to its image.
        pixels: sRGB uint8 array of shape (height, width, 3).
        width: Width in pixels.
        height: Height in pixels.
        source_format: ``"PNG"`` or ``"JPEG"``.
        uploaded_at: When the upload was accepted, from the ``Clock`` port.
    """

    image_id: str
    pixels: NDArray[np.uint8]
    width: int
    height: int
    source_format: str
    uploaded_at: datetime


@dataclass(frozen=True)
class ProcessingSettings:
    """Processing policy that Server Main reads from configuration.

    Attributes:
        threshold: CIEDE2000 confusion threshold. Defaults to 10.
        color_count: Most palette colors that filter 2 extracts. Defaults to 12.
        input_limits: Upload limits. Defaults to 10 MB and 12 megapixels.
    """

    threshold: float = 10.0
    color_count: int = 12
    input_limits: InputLimits = InputLimits()


class Outcome(Enum):
    """What an enhancement achieved. Each value has its own message for the user."""

    ENHANCED = "enhanced"
    NO_CONFUSABLE_PAIRS = "no_confusable_pairs"
    NOT_IMPROVED = "not_improved"


@dataclass(frozen=True)
class PairOutcome:
    """One flagged color pair, as the user sees it.

    Attributes:
        color_a_hex: The first palette color as ``#rrggbb``.
        color_b_hex: The second palette color as ``#rrggbb``.
        before: Simulated CIEDE2000 distance before enhancement.
        after: Simulated CIEDE2000 distance after enhancement.
        improved: True when ``after`` is greater than ``before``.
    """

    color_a_hex: str
    color_b_hex: str
    before: float
    after: float
    improved: bool


@dataclass(frozen=True)
class EnhancementResult:
    """The result of enhancing one session image for one profile.

    Attributes:
        image_id: The ``SessionImage.image_id`` this result belongs to.
        profile: The profile used.
        outcome: What the enhancement achieved.
        message: The outcome in words the user can read.
        palette: Filter 2's palette, reused when only the profile changes.
        mask: bool array of shape (height, width), true for targeted pixels.
        enhanced_pixels: sRGB uint8 array for an ``ENHANCED`` outcome, otherwise None.
        pairs: Each flagged pair and its separation before and after.
        eligible_count: Number of flagged pairs.
        improved_count: Number of flagged pairs whose simulated distance grew.
        newly_confusable_count: Number of pairs that became confusable after enhancement.
    """

    image_id: str
    profile: CvdProfile
    outcome: Outcome
    message: str
    palette: Palette2
    mask: NDArray[np.bool_]
    enhanced_pixels: NDArray[np.uint8] | None
    pairs: tuple[PairOutcome, ...]
    eligible_count: int
    improved_count: int
    newly_confusable_count: int


class View(Enum):
    """Which version of the session image to render."""

    ORIGINAL = "original"
    ENHANCED = "enhanced"

"""Application Core models."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import numpy as np
from numpy.typing import NDArray

from color_engine.models import CvdProfile, InputLimits, Palette2


class UploadRejection(Enum):
    UNSUPPORTED_TYPE = "unsupported_type"
    CORRUPT = "corrupt"
    TOO_LARGE = "too_large"
    TOO_MANY_PIXELS = "too_many_pixels"


@dataclass(frozen=True)
class SessionImage:
    image_id: str
    pixels: NDArray[np.uint8]
    width: int
    height: int
    source_format: str
    uploaded_at: datetime


@dataclass(frozen=True)
class ProcessingSettings:
    threshold: float = 10.0
    color_count: int = 12
    input_limits: InputLimits = InputLimits()


class Outcome(Enum):
    ENHANCED = "enhanced"
    NO_CONFUSABLE_PAIRS = "no_confusable_pairs"
    NOT_IMPROVED = "not_improved"


@dataclass(frozen=True)
class PairOutcome:
    color_a_hex: str
    color_b_hex: str
    before: float
    after: float
    improved: bool


@dataclass(frozen=True)
class EnhancementResult:
    """The result of enhancing one session image for one profile."""

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
    ORIGINAL = "original"
    ENHANCED = "enhanced"

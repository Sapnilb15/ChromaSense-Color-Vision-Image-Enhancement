"""Use case: enhance the session's image for a CVD profile with filters 2 to 5."""

from dataclasses import dataclass

from chromasense.core.errors import NoImageInSession
from chromasense.core.models import (
    EnhancementResult,
    Outcome,
    PairOutcome,
    ProcessingSettings,
)
from chromasense.core.policy.outcome import message_for, outcome_for
from chromasense.core.ports import Clock, SessionImageStore
from color_engine.models import CvdProfile, SeparationReport5
from color_engine.pipeline.filter_2_palette.extract_palette_2 import extract_palette_2
from color_engine.pipeline.filter_3_confusion.detect_confusion_3 import detect_confusion_3
from color_engine.pipeline.filter_4_enhance.enhance_4 import enhance_4
from color_engine.pipeline.filter_5_separation.check_separation_5 import check_separation_5


@dataclass(frozen=True)
class EnhanceImageRequest:
    session_id: str
    profile: CvdProfile


@dataclass(frozen=True)
class EnhanceImageResponse:
    outcome: Outcome
    message: str
    eligible_count: int
    improved_count: int
    pairs: tuple[PairOutcome, ...]


class EnhanceImage:
    def __init__(
        self, store: SessionImageStore, clock: Clock, settings: ProcessingSettings
    ) -> None:
        self._store = store
        self._clock = clock
        self._settings = settings

    def execute(self, request: EnhanceImageRequest) -> EnhanceImageResponse:
        original = self._store.load_original(request.session_id)
        if original is None:
            raise NoImageInSession("Upload an image first.")

        # The palette does not depend on the profile, so reuse it for the same image.
        previous = self._store.load_result(request.session_id)
        if previous is not None and previous.image_id == original.image_id:
            palette = previous.palette
        else:
            palette = extract_palette_2(original.pixels, self._settings.color_count)

        threshold = self._settings.threshold
        confusion = detect_confusion_3(original.pixels, palette, request.profile, threshold)
        enhanced = enhance_4(original.pixels, confusion)
        report = check_separation_5(confusion, enhanced, request.profile, threshold)

        outcome = outcome_for(report)
        result = EnhancementResult(
            image_id=original.image_id,
            profile=request.profile,
            outcome=outcome,
            message=message_for(outcome, report, request.profile),
            palette=palette,
            mask=confusion.mask,
            enhanced_pixels=enhanced.pixels if outcome is Outcome.ENHANCED else None,
            pairs=_pair_outcomes(report, palette.colors_rgb),
            eligible_count=report.eligible_count,
            improved_count=report.improved_count,
            newly_confusable_count=len(report.newly_confusable),
        )
        self._store.save_result(request.session_id, result)
        self._store.touch(request.session_id, self._clock.now())
        return EnhanceImageResponse(
            outcome=result.outcome,
            message=result.message,
            eligible_count=result.eligible_count,
            improved_count=result.improved_count,
            pairs=result.pairs,
        )


def _pair_outcomes(report: SeparationReport5, colors_rgb) -> tuple[PairOutcome, ...]:
    def hex_of(index: int) -> str:
        red, green, blue = (int(channel) for channel in colors_rgb[index])
        return f"#{red:02x}{green:02x}{blue:02x}"

    return tuple(
        PairOutcome(
            color_a_hex=hex_of(pair.a),
            color_b_hex=hex_of(pair.b),
            before=pair.before,
            after=pair.after,
            improved=pair.improved,
        )
        for pair in report.pairs
    )

import pytest

from chromasense.core.models import Outcome
from chromasense.core.policy.outcome import message_for, outcome_for
from color_engine.models import CvdProfile, CvdType, PairSeparation, SeparationReport5

PROFILE = CvdProfile(CvdType.PROTAN, 0.8)


def _report(eligible, improved):
    pairs = tuple(
        PairSeparation(
            a=0, b=i + 1, before=5.0, after=12.0 if i < improved else 4.0, improved=i < improved
        )
        for i in range(eligible)
    )
    return SeparationReport5(
        pairs=pairs, newly_confusable=(), eligible_count=eligible, improved_count=improved
    )


@pytest.mark.parametrize(
    ("eligible", "improved", "outcome"),
    [(0, 0, Outcome.NO_CONFUSABLE_PAIRS), (2, 0, Outcome.NOT_IMPROVED), (2, 1, Outcome.ENHANCED)],
)
def test_outcome_for(eligible, improved, outcome):
    assert outcome_for(_report(eligible, improved)) is outcome


def test_no_pairs_message_names_profile_and_severity():
    message = message_for(Outcome.NO_CONFUSABLE_PAIRS, _report(0, 0), PROFILE)
    assert message == (
        "No colors likely to be confused were found for the protan profile at severity 0.8. "
        "The original image is unchanged."
    )


@pytest.mark.parametrize(
    ("eligible", "improved", "expected"),
    [
        (3, 3, "Adjusted 3 of 3 color pairs likely to be confused."),
        (3, 2, "Adjusted 2 of 3 color pairs likely to be confused. 1 pair could not be improved."),
        (4, 1, "Adjusted 1 of 4 color pairs likely to be confused. 3 pairs could not be improved."),
    ],
)
def test_enhanced_message_counts_pairs(eligible, improved, expected):
    assert message_for(Outcome.ENHANCED, _report(eligible, improved), PROFILE) == expected


@pytest.mark.parametrize("outcome", list(Outcome))
def test_messages_make_no_medical_or_perception_claims(outcome):
    message = message_for(outcome, _report(2, 1), PROFILE).lower()
    for phrase in ("diagnos", "medical", "cure", "correct your vision", "see what"):
        assert phrase not in message

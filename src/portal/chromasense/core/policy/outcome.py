"""Policy: turn a separation report into an outcome and the message the user reads.

Messages name the profile and severity and make no claim about diagnosis or about exactly
what typical color vision sees.
"""

from chromasense.core.models import Outcome
from color_engine.models import CvdProfile, SeparationReport5


def outcome_for(report: SeparationReport5) -> Outcome:
    """Decide the outcome of an enhancement from filter 5's report.

    Args:
        report: Filter 5's separation report.

    Returns:
        ``NO_CONFUSABLE_PAIRS`` when no pair was flagged, ``NOT_IMPROVED`` when no flagged
        pair improved, and ``ENHANCED`` otherwise.
    """
    if report.eligible_count == 0:
        return Outcome.NO_CONFUSABLE_PAIRS
    if report.improved_count == 0:
        return Outcome.NOT_IMPROVED
    return Outcome.ENHANCED


def message_for(outcome: Outcome, report: SeparationReport5, profile: CvdProfile) -> str:
    """Write the status message the user reads for an outcome.

    Args:
        outcome: The outcome from ``outcome_for``.
        report: The same separation report, for the pair counts.
        profile: The profile used, named in the no-pairs message.

    Returns:
        A plain-language message that makes no diagnostic or exact-perception claim.
    """
    if outcome is Outcome.NO_CONFUSABLE_PAIRS:
        return (
            f"No colors likely to be confused were found for the {profile.type.value} profile "
            f"at severity {profile.severity:g}. The original image is unchanged."
        )
    if outcome is Outcome.NOT_IMPROVED:
        return (
            "Colors likely to be confused were found, but the adjustment could not increase "
            "their separation. The original image is still available."
        )
    message = (
        f"Adjusted {report.improved_count} of {report.eligible_count} color pairs likely to "
        "be confused."
    )
    not_improved = report.eligible_count - report.improved_count
    if not_improved:
        noun = "pair" if not_improved == 1 else "pairs"
        message += f" {not_improved} {noun} could not be improved."
    return message

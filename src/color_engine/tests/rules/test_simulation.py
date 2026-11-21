"""Machado (2009) simulation against DaltonLens as an independent reference."""

import numpy as np
import pytest
from daltonlens import simulate as daltonlens

from color_engine.models import CvdProfile, CvdType
from color_engine.rules.simulation import _machado_tables, machado_matrix, simulate

REFERENCE = daltonlens.Simulator_Machado2009()
DEFICIENCY = {
    CvdType.PROTAN: daltonlens.Deficiency.PROTAN,
    CvdType.DEUTAN: daltonlens.Deficiency.DEUTAN,
}


def _random_image() -> np.ndarray:
    return np.random.default_rng(0).integers(0, 256, size=(64, 64, 3), dtype=np.uint8)


def _red_green_image() -> np.ndarray:
    image = np.zeros((32, 64, 3), dtype=np.uint8)
    image[:, :32] = (200, 40, 40)
    image[:, 32:] = (40, 160, 40)
    return image


def _mean_difference(first: np.ndarray, second: np.ndarray) -> float:
    return float(np.mean(np.abs(first.astype(np.float64) - second.astype(np.float64))) / 255.0)


@pytest.mark.parametrize("cvd_type", [CvdType.PROTAN, CvdType.DEUTAN])
@pytest.mark.parametrize("severity", [0.3, 0.7, 1.0])
@pytest.mark.parametrize("make_image", [_random_image, _red_green_image])
def test_matches_daltonlens_within_one_percent(cvd_type, severity, make_image):
    image = make_image()
    ours = simulate(image, CvdProfile(cvd_type, severity))
    reference = REFERENCE.simulate_cvd(image, DEFICIENCY[cvd_type], severity=severity)
    assert _mean_difference(ours, reference) < 0.01


@pytest.mark.parametrize("cvd_type", [CvdType.PROTAN, CvdType.DEUTAN])
def test_primaries_match_daltonlens_within_one_unit(cvd_type):
    primaries = np.array([[[255, 0, 0], [0, 255, 0], [0, 0, 255]]], dtype=np.uint8)
    ours = simulate(primaries, CvdProfile(cvd_type, 1.0)).astype(int)
    reference = REFERENCE.simulate_cvd(primaries, DEFICIENCY[cvd_type], severity=1.0).astype(int)
    assert np.max(np.abs(ours - reference)) <= 1


@pytest.mark.parametrize("cvd_type", [CvdType.PROTAN, CvdType.DEUTAN])
@pytest.mark.parametrize("severity", [0.0, 0.25, 0.5, 1.0])
def test_gray_stays_gray(cvd_type, severity):
    gray = np.full((1, 1, 3), 128, dtype=np.uint8)
    result = simulate(gray, CvdProfile(cvd_type, severity))
    assert np.max(np.abs(result.astype(int) - 128)) <= 1
    assert np.ptp(result) <= 1


@pytest.mark.parametrize("cvd_type", [CvdType.PROTAN, CvdType.DEUTAN])
def test_severity_zero_returns_input(cvd_type):
    image = _random_image()
    result = simulate(image, CvdProfile(cvd_type, 0.0))
    np.testing.assert_array_equal(result, image)
    assert result is not image


@pytest.mark.parametrize("cvd_type", [CvdType.PROTAN, CvdType.DEUTAN])
def test_interpolates_linearly_between_table_steps(cvd_type):
    tables = _machado_tables()[cvd_type.value]
    np.testing.assert_allclose(machado_matrix(cvd_type, 0.45), (tables[4] + tables[5]) / 2)
    np.testing.assert_allclose(machado_matrix(cvd_type, 0.5), tables[5])
    np.testing.assert_allclose(machado_matrix(cvd_type, 1.0), tables[10])


def test_red_green_become_close_under_deutan():
    image = _red_green_image()
    result = simulate(image, CvdProfile(CvdType.DEUTAN, 1.0)).astype(int)
    assert (
        np.abs(result[0, 0] - result[0, 63]).sum()
        < np.abs(image[0, 0].astype(int) - image[0, 63]).sum()
    )


def test_rejects_non_uint8_or_non_rgb_input():
    with pytest.raises(ValueError):
        simulate(np.zeros((2, 2, 3), dtype=np.float64), CvdProfile(CvdType.PROTAN, 1.0))
    with pytest.raises(ValueError):
        simulate(np.zeros((2, 2, 4), dtype=np.uint8), CvdProfile(CvdType.PROTAN, 1.0))


@pytest.mark.parametrize("severity", [-0.1, 1.1])
def test_profile_rejects_severity_outside_range(severity):
    with pytest.raises(ValueError):
        CvdProfile(CvdType.PROTAN, severity)

import numpy as np

from color_engine.rules.color_spaces import (
    lab_to_rgb,
    linear_to_srgb,
    rgb_to_lab,
    srgb_to_linear,
)


def test_transfer_function_round_trip():
    values = np.linspace(0.0, 1.0, 1001)
    np.testing.assert_allclose(linear_to_srgb(srgb_to_linear(values)), values, atol=1e-6)


def test_uint8_input_is_scaled_before_linearizing():
    np.testing.assert_allclose(srgb_to_linear(np.array([0, 255], dtype=np.uint8)), [0.0, 1.0])


def test_known_linear_values():
    # sRGB 0.04045 is the linear segment's end, and sRGB 0.5 is about 0.2140 in linear light.
    np.testing.assert_allclose(
        srgb_to_linear(np.array([0.04045, 0.5])), [0.0031308, 0.21404], atol=1e-5
    )


def test_linear_to_srgb_clips_out_of_range_values():
    np.testing.assert_allclose(linear_to_srgb(np.array([-0.2, 1.4])), [0.0, 1.0])


def test_lab_round_trip_for_every_gray_and_primaries():
    grays = np.repeat(np.arange(256, dtype=np.uint8)[:, None], 3, axis=1)
    primaries = np.array(
        [[255, 0, 0], [0, 255, 0], [0, 0, 255], [200, 40, 40], [40, 160, 40]], dtype=np.uint8
    )
    for colors in (grays, primaries):
        np.testing.assert_array_equal(lab_to_rgb(rgb_to_lab(colors)), colors)


def test_white_and_black_lab():
    lab = rgb_to_lab(np.array([[255, 255, 255], [0, 0, 0]], dtype=np.uint8))
    # scikit-image's D65 white point leaves sRGB white about 0.005 off neutral in a and b.
    np.testing.assert_allclose(lab, [[100.0, 0.0, 0.0], [0.0, 0.0, 0.0]], atol=1e-2)


def test_lab_to_rgb_clips_out_of_gamut():
    rgb = lab_to_rgb(np.array([[50.0, 120.0, -120.0]]))
    assert rgb.dtype == np.uint8
    assert rgb.min() >= 0 and rgb.max() <= 255

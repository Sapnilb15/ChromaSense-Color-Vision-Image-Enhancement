import importlib.util
import io
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageFile

from color_engine.models import DecodeError, DecodeReason, InputLimits
from color_engine.pipeline.filter_1_decode.decode_1 import decode_1
from color_engine.rules.color_spaces import linear_to_srgb, srgb_to_linear

SAMPLES = Path(__file__).resolve().parents[1] / "data" / "samples"
LIMITS = InputLimits()

# sRGB colorants adapted to D50 (Lindbloom), as LittleCMS uses for its built-in sRGB profile.
SRGB_D50 = np.array(
    [
        [0.4360747, 0.3850649, 0.1430804],
        [0.2225045, 0.7168786, 0.0606169],
        [0.0139322, 0.0971045, 0.7141733],
    ]
)


def _sample(name: str) -> bytes:
    return (SAMPLES / name).read_bytes()


def _samples_module():
    spec = importlib.util.spec_from_file_location("make_samples", SAMPLES / "make_samples.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _encode(image: Image.Image, image_format: str, **options) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, image_format, **options)
    return buffer.getvalue()


@pytest.mark.parametrize(("name", "image_format"), [("valid.png", "PNG"), ("valid.jpg", "JPEG")])
def test_valid_png_and_jpeg_decode_to_uint8_rgb(name, image_format):
    decoded = decode_1(_sample(name), LIMITS)
    assert (decoded.width, decoded.height) == (60, 40)
    assert decoded.pixels.shape == (40, 60, 3)
    assert decoded.pixels.dtype == np.uint8
    assert decoded.source_format == image_format


def test_png_pixels_are_exact():
    pixels = decode_1(_sample("valid.png"), LIMITS).pixels
    assert tuple(pixels[10, 5]) == (200, 40, 40)
    assert tuple(pixels[10, 25]) == (40, 160, 40)
    assert tuple(pixels[10, 50]) == (128, 128, 128)


@pytest.mark.parametrize(
    ("name", "reason"),
    [
        ("not_an_image.png", DecodeReason.UNSUPPORTED_TYPE),
        ("truncated.jpg", DecodeReason.CORRUPT),
        ("over_12mp.png", DecodeReason.TOO_MANY_PIXELS),
    ],
)
def test_invalid_samples_are_rejected_with_reason(name, reason):
    with pytest.raises(DecodeError) as caught:
        decode_1(_sample(name), LIMITS)
    assert caught.value.reason is reason


def test_bytes_over_ten_megabytes_are_too_large():
    data = _sample("valid.png") + b"\0" * (10 * 1024 * 1024)
    with pytest.raises(DecodeError) as caught:
        decode_1(data, LIMITS)
    assert caught.value.reason is DecodeReason.TOO_LARGE


def test_exactly_ten_megabytes_is_not_too_large():
    data = _sample("valid.png")
    limits = InputLimits(max_bytes=len(data))
    assert decode_1(data, limits).width == 60


def test_over_12_megapixels_is_rejected_before_pixels_are_decoded(monkeypatch):
    def fail_load(self):
        raise AssertionError("pixel data was decoded")

    monkeypatch.setattr(ImageFile.ImageFile, "load", fail_load)
    with pytest.raises(DecodeError) as caught:
        decode_1(_sample("over_12mp.png"), LIMITS)
    assert caught.value.reason is DecodeReason.TOO_MANY_PIXELS


def test_exactly_12_megapixels_is_accepted():
    data = _encode(Image.new("RGB", (4000, 3000), (10, 20, 30)), "PNG")
    decoded = decode_1(data, LIMITS)
    assert decoded.width * decoded.height == 12_000_000


@pytest.mark.parametrize("image_format", ["GIF", "BMP", "WEBP", "TIFF"])
def test_other_image_formats_are_unsupported(image_format):
    data = _encode(Image.new("RGB", (8, 8), (1, 2, 3)), image_format)
    with pytest.raises(DecodeError) as caught:
        decode_1(data, LIMITS)
    assert caught.value.reason is DecodeReason.UNSUPPORTED_TYPE


def test_png_with_a_jpeg_name_is_judged_by_content():
    # The file name never reaches decode_1; only the bytes matter.
    assert decode_1(_sample("valid.png"), LIMITS).source_format == "PNG"


def test_animated_png_is_unsupported():
    frames = [Image.new("RGB", (8, 8), color) for color in ((255, 0, 0), (0, 0, 255))]
    data = _encode(frames[0], "PNG", save_all=True, append_images=frames[1:])
    with pytest.raises(DecodeError) as caught:
        decode_1(data, LIMITS)
    assert caught.value.reason is DecodeReason.UNSUPPORTED_TYPE


def test_display_p3_jpeg_is_converted_to_srgb():
    module = _samples_module()
    p3 = np.array(module.P3_SAMPLE_COLOR) / 255.0
    xyz = np.array(module.DISPLAY_P3_D50) @ srgb_to_linear(p3)
    expected = linear_to_srgb(np.linalg.solve(SRGB_D50, xyz)) * 255.0

    pixel = decode_1(_sample("display_p3.jpg"), LIMITS).pixels[32, 32].astype(float)

    assert np.max(np.abs(pixel - expected)) <= 2
    # The conversion must actually change the values, or the profile was ignored.
    assert np.max(np.abs(pixel - np.array(module.P3_SAMPLE_COLOR))) > 5


def test_exif_orientation_is_applied():
    decoded = decode_1(_sample("exif_rotated.jpg"), LIMITS)
    # Stored 40 x 20 with red on the left; rotated 90 degrees clockwise, red is on top.
    assert (decoded.width, decoded.height) == (20, 40)
    top, bottom = decoded.pixels[5, 10].astype(int), decoded.pixels[35, 10].astype(int)
    assert top[0] > 150 and top[2] < 90
    assert bottom[2] > 150 and bottom[0] < 90


def test_transparent_png_is_composited_on_white():
    image = Image.new("RGBA", (4, 4), (0, 0, 0, 0))
    image.putpixel((0, 0), (200, 40, 40, 255))
    pixels = decode_1(_encode(image, "PNG"), LIMITS).pixels
    assert tuple(pixels[0, 0]) == (200, 40, 40)
    assert tuple(pixels[3, 3]) == (255, 255, 255)


@pytest.mark.parametrize("mode", ["L", "P", "LA", "I;16", "CMYK"])
def test_other_pixel_modes_become_rgb(mode):
    image_format = "JPEG" if mode == "CMYK" else "PNG"
    image = Image.new("RGB", (6, 6), (90, 90, 90)).convert(mode)
    pixels = decode_1(_encode(image, image_format), LIMITS).pixels
    assert pixels.shape == (6, 6, 3)
    assert pixels.dtype == np.uint8


def test_sixteen_bit_gray_is_scaled_to_eight_bits():
    image = Image.fromarray(np.full((4, 4), 65535, dtype=np.uint16))
    pixels = decode_1(_encode(image, "PNG"), LIMITS).pixels
    assert tuple(pixels[0, 0]) == (255, 255, 255)


def test_empty_bytes_are_unsupported():
    with pytest.raises(DecodeError) as caught:
        decode_1(b"", LIMITS)
    assert caught.value.reason is DecodeReason.UNSUPPORTED_TYPE

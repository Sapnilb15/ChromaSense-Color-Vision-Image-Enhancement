import io

import numpy as np
import pytest
from PIL import Image

from color_engine.rules.encode import encode_png


def test_png_round_trip_is_lossless():
    pixels = np.random.default_rng(1).integers(0, 256, size=(37, 53, 3), dtype=np.uint8)
    data = encode_png(pixels)
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    with Image.open(io.BytesIO(data)) as image:
        assert image.format == "PNG"
        assert image.mode == "RGB"
        np.testing.assert_array_equal(np.asarray(image), pixels)


@pytest.mark.parametrize(
    "pixels",
    [np.zeros((4, 4), dtype=np.uint8), np.zeros((4, 4, 4), dtype=np.uint8), np.zeros((4, 4, 3))],
)
def test_rejects_wrong_shape_or_type(pixels):
    with pytest.raises(ValueError):
        encode_png(pixels)

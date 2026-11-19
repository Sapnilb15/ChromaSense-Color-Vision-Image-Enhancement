"""Regenerate the decode fixtures in this folder.

Run from the repository root: python src/color_engine/tests/data/samples/make_samples.py
The files are committed, so tests and later increments read them without running this script.
"""

import io
import struct
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent

# Display P3 colorants adapted to the D50 profile connection space (columns R, G, B).
DISPLAY_P3_D50 = (
    (0.515102, 0.291965, 0.157153),
    (0.241196, 0.692236, 0.066568),
    (-0.001053, 0.041882, 0.784073),
)
D50_WHITE = (0.9642, 1.0, 0.8249)
# The Display P3 color stored in display_p3.jpg, in P3 code values.
P3_SAMPLE_COLOR = (180, 120, 60)


def display_p3_icc() -> bytes:
    """Build a minimal ICC v2 RGB matrix/TRC profile for Display P3 with the sRGB curve."""

    def s15f16(value: float) -> bytes:
        return struct.pack(">i", round(value * 65536))

    def xyz(values: tuple[float, float, float]) -> bytes:
        return b"XYZ " + b"\0" * 4 + b"".join(s15f16(v) for v in values)

    # Parametric curve type 3 is the sRGB transfer function.
    curve = (
        b"para"
        + b"\0" * 4
        + struct.pack(">HH", 3, 0)
        + b"".join(s15f16(v) for v in (2.4, 1 / 1.055, 0.055 / 1.055, 1 / 12.92, 0.04045))
    )
    name = b"Display P3 test profile\0"
    desc = (
        b"desc"
        + b"\0" * 4
        + struct.pack(">I", len(name))
        + name
        + struct.pack(">II", 0, 0)
        + struct.pack(">HB", 0, 0)
        + b"\0" * 67
    )
    columns = list(zip(*DISPLAY_P3_D50, strict=True))
    tags = [
        (b"desc", desc),
        (b"wtpt", xyz(D50_WHITE)),
        (b"rXYZ", xyz(columns[0])),
        (b"gXYZ", xyz(columns[1])),
        (b"bXYZ", xyz(columns[2])),
        (b"rTRC", curve),
        (b"gTRC", curve),
        (b"bTRC", curve),
        (b"cprt", b"text" + b"\0" * 4 + b"No copyright, test data\0"),
    ]

    table_size = 4 + 12 * len(tags)
    offset = 128 + table_size
    entries, payload = b"", b""
    for signature, data in tags:
        padded = data + b"\0" * (-len(data) % 4)
        entries += signature + struct.pack(">II", offset + len(payload), len(data))
        payload += padded
    body = struct.pack(">I", len(tags)) + entries + payload
    size = 128 + len(body)
    header = (
        struct.pack(">I", size)
        + b"lcms"
        + struct.pack(">I", 0x02100000)
        + b"mntrRGB XYZ "
        + b"\0" * 12
        + b"acsp"
        + b"\0" * 24
        + struct.pack(">I", 0)
        + b"".join(s15f16(v) for v in D50_WHITE)
        + b"\0" * 4
        + b"\0" * 16
        + b"\0" * 28
    )
    assert len(header) == 128
    return header + body


def _three_bands() -> Image.Image:
    image = Image.new("RGB", (60, 40), (128, 128, 128))
    image.paste((200, 40, 40), (0, 0, 20, 40))
    image.paste((40, 160, 40), (20, 0, 40, 40))
    return image


def main() -> None:
    _three_bands().save(HERE / "valid.png")
    _three_bands().save(HERE / "valid.jpg", quality=95)

    (HERE / "not_an_image.png").write_text("This is a text file with a .png name.\n")

    jpeg = io.BytesIO()
    Image.new("RGB", (200, 200), (90, 140, 200)).save(jpeg, "JPEG", quality=95)
    (HERE / "truncated.jpg").write_bytes(jpeg.getvalue()[: len(jpeg.getvalue()) // 2])

    # 4100 x 3000 is 12.3 megapixels, just over the limit; a flat color keeps the file small.
    Image.new("RGB", (4100, 3000), (100, 100, 100)).save(HERE / "over_12mp.png", optimize=True)

    Image.new("RGB", (64, 64), P3_SAMPLE_COLOR).save(
        HERE / "display_p3.jpg", quality=100, subsampling=0, icc_profile=display_p3_icc()
    )

    # Stored 40 wide by 20 high; orientation 6 means rotate 90 degrees clockwise to display.
    rotated = Image.new("RGB", (40, 20), (200, 40, 40))
    rotated.paste((40, 40, 200), (20, 0, 40, 20))
    exif = Image.Exif()
    exif[0x0112] = 6
    rotated.save(HERE / "exif_rotated.jpg", quality=95, exif=exif.tobytes())


if __name__ == "__main__":
    main()

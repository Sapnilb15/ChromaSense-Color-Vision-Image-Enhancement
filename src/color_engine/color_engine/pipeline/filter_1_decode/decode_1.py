"""Filter 1: turn uploaded bytes into 8-bit sRGB pixels, or reject them with a reason."""

import struct
import warnings
from io import BytesIO

import numpy as np
from PIL import Image, ImageCms, ImageOps, UnidentifiedImageError

from color_engine.models import DecodedImage1, DecodeError, DecodeReason, InputLimits

_ACCEPTED_FORMATS = ["PNG", "JPEG"]
_DIRECT_PROFILE_MODES = ("RGB", "L", "CMYK")
_DECODE_ERRORS = (OSError, SyntaxError, ValueError, EOFError, struct.error)


def decode_1(data: bytes, limits: InputLimits) -> DecodedImage1:
    if len(data) > limits.max_bytes:
        raise DecodeError(DecodeReason.TOO_LARGE)

    image = _open(data)
    try:
        if getattr(image, "n_frames", 1) > 1:
            raise DecodeError(DecodeReason.UNSUPPORTED_TYPE)
        # Checked from the header, before any pixel data is decoded.
        if image.width * image.height > limits.max_megapixels * 1_000_000:
            raise DecodeError(DecodeReason.TOO_MANY_PIXELS)
        source_format = image.format
        try:
            image.load()
            icc_profile = image.info.get("icc_profile")
            pixels = _to_srgb_pixels(ImageOps.exif_transpose(image), icc_profile)
        except (*_DECODE_ERRORS, ImageCms.PyCMSError) as error:
            raise DecodeError(DecodeReason.CORRUPT) from error
    finally:
        image.close()

    height, width = pixels.shape[:2]
    return DecodedImage1(pixels=pixels, width=width, height=height, source_format=source_format)


def _open(data: bytes) -> Image.Image:
    try:
        with warnings.catch_warnings():
            # The megapixel limit above is far lower than Pillow's own warning threshold.
            warnings.simplefilter("ignore", Image.DecompressionBombWarning)
            return Image.open(BytesIO(data), formats=_ACCEPTED_FORMATS)
    except UnidentifiedImageError as error:
        raise DecodeError(DecodeReason.UNSUPPORTED_TYPE) from error
    except Image.DecompressionBombError as error:
        raise DecodeError(DecodeReason.TOO_MANY_PIXELS) from error
    except _DECODE_ERRORS as error:
        raise DecodeError(DecodeReason.CORRUPT) from error


def _to_srgb_pixels(image: Image.Image, icc_profile: bytes | None) -> np.ndarray:
    alpha = _alpha_channel(image)
    color = _apply_profile(_color_image(image), icc_profile)
    if alpha is None:
        return np.array(color, dtype=np.uint8)
    white = Image.new("RGB", color.size, (255, 255, 255))
    white.paste(color, mask=alpha)
    return np.array(white, dtype=np.uint8)


def _alpha_channel(image: Image.Image) -> Image.Image | None:
    if image.mode in ("RGBA", "LA", "PA") or "transparency" in image.info:
        return image.convert("RGBA").getchannel("A")
    return None


def _color_image(image: Image.Image) -> Image.Image:
    if image.mode.startswith("I;16") or image.mode == "I":
        eight_bit = np.clip(np.asarray(image, dtype=np.int64) >> 8, 0, 255).astype(np.uint8)
        return Image.fromarray(eight_bit)
    if image.mode in _DIRECT_PROFILE_MODES:
        return image
    if image.mode == "LA":
        return image.convert("L")
    return image.convert("RGBA").convert("RGB")


def _apply_profile(image: Image.Image, icc_profile: bytes | None) -> Image.Image:
    if not icc_profile:
        return image.convert("RGB")
    source = ImageCms.ImageCmsProfile(BytesIO(icc_profile))
    return ImageCms.profileToProfile(
        image, source, ImageCms.createProfile("sRGB"), outputMode="RGB"
    )

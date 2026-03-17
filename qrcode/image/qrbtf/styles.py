"""
Qrbtf style factories: A1, A2, C2, SP1.

Each make_qrbtf_* function returns a PIL Image (or image factory result)
for the given data and style options, matching the qrbtf frontend behavior.
"""

from __future__ import annotations

import random
from typing import Any

from qrcode import QRCode, constants
from qrcode.image.styles.colormasks import SolidFillColorMask
from qrcode.image.styles.moduledrawers.pil import (
    CircleModuleDrawer,
    GappedCircleModuleDrawer,
    GappedSquareModuleDrawer,
    RoundedModuleDrawer,
    SquareModuleDrawer,
)
from qrcode.image.styledpil import StyledPilImage
from qrcode.point_types import QRPointType, get_type_table

# Option keys that each image factory accepts (so we don't pass box_size, border, correct_level)
A1_IMAGE_OPTS = frozenset({
    "positioning_point_type", "content_point_type", "content_point_scale",
    "content_point_opacity", "content_point_color", "positioning_point_color",
})
A2_IMAGE_OPTS = frozenset({
    "content_line_type", "content_point_scale", "content_point_opacity",
    "content_point_color", "positioning_point_type", "positioning_point_color",
})
C2_IMAGE_OPTS = frozenset({
    "background_image", "background_path", "contrast", "brightness",
    "align_type", "timing_type",
})
SP1_IMAGE_OPTS = frozenset({
    "content_stroke_width", "content_x_stroke_width", "positioning_stroke_width",
    "positioning_point_type",
})
# Passed only to SVG image factories (A1/A2/SP1 SVG); background embedded in SVG
SVG_BACKGROUND_OPTS = frozenset({"background_path", "background_image"})
# Center logo overlay (drawn on top of QR in SVG)
SVG_LOGO_OPTS = frozenset({"logo_path", "logo_image", "logo_size", "logo_margin"})
# Optional text on one side of the QR (SVG)
SVG_TEXT_OPTS = frozenset({"text", "text_position", "text_color", "text_font_size"})
# SVG view / margin (quiet zone around QR in module units)
SVG_VIEW_OPTS = frozenset({"svg_margin"})

# Default presets matching frontend (a1, a1c, a1p, a2, a2c, c2, sp1)
A1_PRESETS = {
    "a1": {
        "correct_level": constants.ERROR_CORRECT_M,
        "positioning_point_type": "square",
        "content_point_type": "square",
        "content_point_scale": 1.0,
        "content_point_opacity": 1.0,
        "content_point_color": "#000000",
        "positioning_point_color": "#000000",
    },
    "a1c": {
        "correct_level": constants.ERROR_CORRECT_M,
        "positioning_point_type": "circle",
        "content_point_type": "circle",
        "content_point_scale": 0.5,
        "content_point_opacity": 0.3,
        "content_point_color": "#000000",
        "positioning_point_color": "#000000",
    },
    "a1p": {
        "correct_level": constants.ERROR_CORRECT_M,
        "positioning_point_type": "planet",
        "content_point_type": "circle",
        "content_point_scale": 0.0,
        "content_point_opacity": 1.0,
        "content_point_color": "#000000",
        "positioning_point_color": "#000000",
    },
}

A2_PRESETS = {
    "a2": {
        "correct_level": constants.ERROR_CORRECT_M,
        "positioning_point_type": "rounded",
        "content_line_type": "interlock",
        "content_point_scale": 0.6,
        "content_point_opacity": 1.0,
        "content_point_color": "#000000",
        "positioning_point_color": "#000000",
    },
    "a2c": {
        "correct_level": constants.ERROR_CORRECT_M,
        "positioning_point_type": "square",
        "content_line_type": "cross",
        "content_point_scale": 0.6,
        "content_point_opacity": 1.0,
        "content_point_color": "#000000",
        "positioning_point_color": "#000000",
    },
}

SP1_PRESETS = {
    "sp1": {
        "correct_level": constants.ERROR_CORRECT_M,
        "content_stroke_width": 0.7,
        "content_x_stroke_width": 0.7,
        "positioning_stroke_width": 0.9,
        "positioning_point_type": "dsj",
    },
}


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    if len(h) == 6:
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    if len(h) == 3:
        return (int(h[0] * 2, 16), int(h[1] * 2, 16), int(h[2] * 2, 16))
    return (0, 0, 0)


def make_qrbtf_a1(
    data: str,
    preset: str = "a1",
    box_size: int = 10,
    border: int = 4,
    **kwargs: Any,
):
    """
    A1-style QR: square/circle/planet/rounded finders, scalable content modules.
    Presets: a1, a1c, a1p (same as frontend).
    """
    options = {**A1_PRESETS.get(preset, A1_PRESETS["a1"]), **kwargs}
    pos_type = options.get("positioning_point_type", "square")
    content_type = options.get("content_point_type", "square")
    content_scale = options.get("content_point_scale", 1.0)
    fg = _hex_to_rgb(options.get("content_point_color", "#000000"))
    bg = (255, 255, 255)

    if pos_type == "rounded":
        eye_drawer = RoundedModuleDrawer(radius_ratio=1)
    elif pos_type == "circle" or pos_type == "planet":
        eye_drawer = CircleModuleDrawer()
    else:
        eye_drawer = SquareModuleDrawer()

    if content_type == "circle":
        size_ratio = max(0.01, content_scale) if content_scale > 0 else 0.5
        module_drawer = GappedCircleModuleDrawer(size_ratio=size_ratio)
    else:
        size_ratio = max(0.01, content_scale) if content_scale > 0 else 0.8
        module_drawer = GappedSquareModuleDrawer(size_ratio=size_ratio)

    color_mask = SolidFillColorMask(back_color=bg, front_color=fg)
    qr = QRCode(
        error_correction=options.get("correct_level", constants.ERROR_CORRECT_M),
        box_size=box_size,
        border=border,
        image_factory=StyledPilImage,
    )
    qr.add_data(data)
    return qr.make_image(
        module_drawer=module_drawer,
        eye_drawer=eye_drawer,
        color_mask=color_mask,
    )


def make_qrbtf_a2(
    data: str,
    preset: str = "a2",
    box_size: int = 10,
    border: int = 4,
    **kwargs: Any,
):
    """
    A2-style QR: line-based content (horizontal, vertical, interlock, etc.).
    Presets: a2, a2c. Uses A2StyledPilImage for line grouping.
    """
    from qrcode.image.qrbtf.a2 import A2StyledPilImage

    options = {**A2_PRESETS.get(preset, A2_PRESETS["a2"]), **kwargs}
    qr = QRCode(
        error_correction=options.get("correct_level", constants.ERROR_CORRECT_M),
        box_size=box_size,
        border=border,
        image_factory=A2StyledPilImage,
    )
    qr.add_data(data)
    image_opts = {k: v for k, v in options.items() if k in A2_IMAGE_OPTS}
    return qr.make_image(**image_opts)


def make_qrbtf_c2(
    data: str,
    background_image=None,
    background_path: str | None = None,
    contrast: float = 0.0,
    brightness: float = 0.0,
    align_type: str = "none",
    timing_type: str = "none",
    box_size: int = 10,
    border: int = 4,
    **kwargs: Any,
):
    """
    C2-style QR: image background with contrast/brightness dithering.
    Different module sizes for finder (B) vs data (S). Requires PIL.
    """
    from qrcode.image.qrbtf.c2 import C2StyledPilImage

    qr = QRCode(
        error_correction=constants.ERROR_CORRECT_H,
        box_size=box_size,
        border=border,
        image_factory=C2StyledPilImage,
    )
    qr.add_data(data)
    image_opts = {k: v for k, v in kwargs.items() if k in C2_IMAGE_OPTS}
    return qr.make_image(
        background_image=background_image,
        background_path=background_path,
        contrast=contrast,
        brightness=brightness,
        align_type=align_type,
        timing_type=timing_type,
        **image_opts,
    )


def make_qrbtf_sp1(
    data: str,
    preset: str = "sp1",
    box_size: int = 10,
    border: int = 4,
    **kwargs: Any,
):
    """
    SP1-style QR: DSJ or square finder, vertical/horizontal bars, X-marks.
    Presets: sp1.
    """
    from qrcode.image.qrbtf.sp1 import SP1StyledPilImage

    options = {**SP1_PRESETS.get(preset, SP1_PRESETS["sp1"]), **kwargs}
    qr = QRCode(
        error_correction=options.get("correct_level", constants.ERROR_CORRECT_M),
        box_size=box_size,
        border=border,
        image_factory=SP1StyledPilImage,
    )
    qr.add_data(data)
    image_opts = {k: v for k, v in options.items() if k in SP1_IMAGE_OPTS}
    return qr.make_image(**image_opts)


def make_qrbtf_a1_svg(
    data: str,
    preset: str = "a1",
    box_size: int = 10,
    border: int = 4,
    **kwargs: Any,
):
    """A1-style QR as SVG (vector output)."""
    from qrcode.image.qrbtf.svg import A1SvgImage

    options = {**A1_PRESETS.get(preset, A1_PRESETS["a1"]), **kwargs}
    qr = QRCode(
        error_correction=options.get("correct_level", constants.ERROR_CORRECT_M),
        box_size=box_size,
        border=border,
        image_factory=A1SvgImage,
    )
    qr.add_data(data)
    image_opts = {
        k: v for k, v in options.items()
        if k in A1_IMAGE_OPTS or k in SVG_BACKGROUND_OPTS or k in SVG_LOGO_OPTS or k in SVG_TEXT_OPTS or k in SVG_VIEW_OPTS
    }
    return qr.make_image(**image_opts)


def make_qrbtf_a2_svg(
    data: str,
    preset: str = "a2",
    box_size: int = 10,
    border: int = 4,
    **kwargs: Any,
):
    """A2-style QR as SVG (vector output)."""
    from qrcode.image.qrbtf.svg import A2SvgImage

    options = {**A2_PRESETS.get(preset, A2_PRESETS["a2"]), **kwargs}
    qr = QRCode(
        error_correction=options.get("correct_level", constants.ERROR_CORRECT_M),
        box_size=box_size,
        border=border,
        image_factory=A2SvgImage,
    )
    qr.add_data(data)
    image_opts = {
        k: v for k, v in options.items()
        if k in A2_IMAGE_OPTS or k in SVG_BACKGROUND_OPTS or k in SVG_LOGO_OPTS or k in SVG_TEXT_OPTS or k in SVG_VIEW_OPTS
    }
    return qr.make_image(**image_opts)


def make_qrbtf_sp1_svg(
    data: str,
    preset: str = "sp1",
    box_size: int = 10,
    border: int = 4,
    **kwargs: Any,
):
    """SP1-style QR as SVG (vector output). C2 is image-based and has no SVG."""
    from qrcode.image.qrbtf.svg import SP1SvgImage

    options = {**SP1_PRESETS.get(preset, SP1_PRESETS["sp1"]), **kwargs}
    qr = QRCode(
        error_correction=options.get("correct_level", constants.ERROR_CORRECT_M),
        box_size=box_size,
        border=border,
        image_factory=SP1SvgImage,
    )
    qr.add_data(data)
    image_opts = {
        k: v for k, v in options.items()
        if k in SP1_IMAGE_OPTS or k in SVG_BACKGROUND_OPTS or k in SVG_LOGO_OPTS or k in SVG_TEXT_OPTS or k in SVG_VIEW_OPTS
    }
    return qr.make_image(**image_opts)

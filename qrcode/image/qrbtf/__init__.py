"""
Qrbtf-style QR code renderers.

Provides the same visual styles as the qrbtf frontend:
- A1: Square/circle/planet/rounded finders, scalable content modules
- A2: Line-based content (horizontal, vertical, interlock, etc.) with dots
- C2: Image background with contrast/brightness dithering
- SP1: DSJ finder, vertical/horizontal bars, X-marks in 2x2/3x3 blocks
"""

from __future__ import annotations

from qrcode.image.qrbtf.styles import (
    make_qrbtf_a1,
    make_qrbtf_a2,
    make_qrbtf_c2,
    make_qrbtf_sp1,
    make_qrbtf_a1_svg,
    make_qrbtf_a2_svg,
    make_qrbtf_sp1_svg,
)

__all__ = [
    "make_qrbtf_a1",
    "make_qrbtf_a2",
    "make_qrbtf_c2",
    "make_qrbtf_sp1",
    "make_qrbtf_a1_svg",
    "make_qrbtf_a2_svg",
    "make_qrbtf_sp1_svg",
]

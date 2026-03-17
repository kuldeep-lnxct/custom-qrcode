"""
C2-style QR: image background with contrast/brightness threshold.
Finder modules drawn large (B), data modules small (S). Uses gamma-like
luminance and random threshold for background dithering.
"""

from __future__ import annotations

import random

from PIL import Image

import qrcode.image.base
from qrcode.point_types import QRPointType, get_type_table


def _gamma(r: int, g: int, b: int) -> float:
    """Luminance similar to qrbtf frontend image_utils.gamma."""
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    return (
        (r**2.2 + (1.5 * g) ** 2.2 + (0.6 * b) ** 2.2)
        / (1 + 1.5**2.2 + 0.6**2.2)
    ) ** (1 / 2.2)


class C2StyledPilImage(qrcode.image.base.BaseImage):
    """Renders QR with C2 style: image background + contrast/brightness dithering."""

    kind = "PNG"
    needs_drawrect = False
    needs_processing = True

    def __init__(self, *args, **kwargs):
        self.background_image = kwargs.pop("background_image", None)
        self.background_path = kwargs.pop("background_path", None)
        self.contrast = kwargs.pop("contrast", 0.0)
        self.brightness = kwargs.pop("brightness", 0.0)
        self.align_type = kwargs.pop("align_type", "none")
        self.timing_type = kwargs.pop("timing_type", "none")
        super().__init__(*args, **kwargs)

    def _load_background(self, bg, size: int) -> Image.Image:
        """Load and prepare background: center-crop to square then resize to size."""
        if not isinstance(bg, Image.Image):
            bg = Image.open(bg)
        bg = bg.convert("RGB")
        w, h = bg.size
        if w != h:
            # Center-crop to square
            s = min(w, h)
            left = (w - s) // 2
            top = (h - s) // 2
            bg = bg.crop((left, top, left + s, top + s))
        return bg.resize((size, size), Image.Resampling.LANCZOS)

    def new_image(self, **kwargs):
        size = self.pixel_size
        if self.background_image is not None:
            bg = self._load_background(self.background_image, size)
            return bg.copy()
        if self.background_path:
            bg = self._load_background(self.background_path, size)
            return bg.copy()
        return Image.new("RGB", (size, size), (255, 255, 255))

    def drawrect(self, row, col):
        pass

    def process(self):
        n = self.width
        table = self.modules
        type_table = get_type_table(n)
        box_size = self.box_size
        border = self.border
        pix = self._img.load()
        w, h = self._img.size

        # Optional dither: darken pixels by contrast/brightness threshold
        for px in range(w):
            for py in range(h):
                r, g, b = self._img.getpixel((px, py))[:3]
                gray = _gamma(r, g, b)
                threshold = (gray + self.brightness - 0.5) * (self.contrast + 1) + 0.5
                if random.random() > threshold:
                    pix[px, py] = (0, 0, 0)

        # Draw modules: finder = big (B ~3.08), data = small (S ~1.02)
        for row in range(n):
            for col in range(n):
                if not table[row][col]:
                    continue
                pt = type_table[row][col]
                cx = border * box_size + (col + 0.5) * box_size
                cy = border * box_size + (row + 0.5) * box_size
                if pt in (QRPointType.POS_CENTER, QRPointType.POS_OTHER):
                    self._draw_big_module(pix, cx, cy, box_size)
                else:
                    if pt in (QRPointType.ALIGN_CENTER, QRPointType.ALIGN_OTHER):
                        if self.align_type == "black-white":
                            self._draw_big_module(pix, cx, cy, box_size)
                        else:
                            self._draw_small_module_at(pix, cx, cy, box_size)
                    elif pt == QRPointType.TIMING:
                        if self.timing_type == "black-white":
                            self._draw_big_module(pix, cx, cy, box_size)
                        else:
                            self._draw_small_module_at(pix, cx, cy, box_size)
                    else:
                        self._draw_small_module_at(pix, cx, cy, box_size)

    def _draw_big_module(self, pix, cx, cy, box_size):
        # B: 3.08 units -> about 1.54 * box_size radius
        r = 1.54 * box_size
        for dx in range(-int(r), int(r) + 1):
            for dy in range(-int(r), int(r) + 1):
                if dx * dx + dy * dy <= r * r:
                    x = int(cx + dx)
                    y = int(cy + dy)
                    if 0 <= x < self._img.width and 0 <= y < self._img.height:
                        pix[x, y] = (0, 0, 0)

    def _draw_small_module_at(self, pix, cx, cy, box_size):
        # S: 1.02 units -> about 0.51 * box_size
        h = 0.51 * box_size
        for dx in range(-int(h), int(h) + 1):
            for dy in range(-int(h), int(h) + 1):
                x = int(cx + dx)
                y = int(cy + dy)
                if 0 <= x < self._img.width and 0 <= y < self._img.height:
                    pix[x, y] = (0, 0, 0)

    def save(self, stream, format=None, **kwargs):
        if format is None:
            format = self.kind
        self._img.save(stream, format=format, **kwargs)

    def __getattr__(self, name):
        return getattr(self._img, name)

"""
A2-style QR: line-based content (horizontal, vertical, interlock, radial, etc.)
with dots for single modules. Renders in process() after a no-op drawrect pass.
"""

from __future__ import annotations

from PIL import Image, ImageDraw

import qrcode.image.base
from qrcode.point_types import QRPointType, get_type_table


class A2StyledPilImage(qrcode.image.base.BaseImage):
    """Renders QR with A2 style: finder patterns + line groups + dots."""

    kind = "PNG"
    needs_drawrect = False
    needs_processing = True

    def __init__(self, *args, **kwargs):
        self.content_line_type = kwargs.pop("content_line_type", "interlock")
        self.content_point_scale = kwargs.pop("content_point_scale", 0.6)
        self.content_point_opacity = kwargs.pop("content_point_opacity", 1.0)
        self.content_point_color = kwargs.pop("content_point_color", "#000000")
        self.positioning_point_type = kwargs.pop("positioning_point_type", "rounded")
        self.positioning_point_color = kwargs.pop("positioning_point_color", "#000000")
        super().__init__(*args, **kwargs)

    def new_image(self, **kwargs):
        return Image.new("RGB", (self.pixel_size, self.pixel_size), (255, 255, 255))

    def drawrect(self, row, col):
        pass

    def process(self):
        n = self.width
        table = self.modules
        type_table = get_type_table(n)
        draw = ImageDraw.Draw(self._img)
        box_size = self.box_size
        border = self.border

        def to_px(x, y):
            return (
                border * box_size + x * box_size,
                border * box_size + y * box_size,
            )

        def fill_rect(cx, cy, w, h, color):
            x0 = border * box_size + (cx - w / 2) * box_size
            y0 = border * box_size + (cy - h / 2) * box_size
            draw.rectangle(
                [x0, y0, x0 + w * box_size, y0 + h * box_size],
                fill=color,
                outline=None,
            )

        def draw_line(x1, y1, x2, y2, stroke, color):
            px1, py1 = to_px(x1, y1)
            px2, py2 = to_px(x2, y2)
            half = stroke * box_size / 2
            draw.line([px1, py1, px2, py2], fill=color, width=int(stroke * box_size))

        color = self.content_point_color
        if isinstance(color, str) and color.startswith("#"):
            color = tuple(int(color[i : i + 2], 16) for i in (1, 3, 5))
        elif not isinstance(color, (tuple, list)) or len(color) != 3:
            color = (0, 0, 0)
        pos_color = self.positioning_point_color
        if isinstance(pos_color, str) and pos_color.startswith("#"):
            pos_color = tuple(int(pos_color[i : i + 2], 16) for i in (1, 3, 5))
        elif not isinstance(pos_color, (tuple, list)) or len(pos_color) != 3:
            pos_color = (0, 0, 0)

        size = self.content_point_scale
        available = [[True] * n for _ in range(n)]
        ava2 = [[True] * n for _ in range(n)]

        # Draw finders (positioning)
        for y in range(n):
            for x in range(n):
                if type_table[y][x] != QRPointType.POS_CENTER:
                    continue
                if not table[y][x]:
                    continue
                if self.positioning_point_type == "square":
                    fill_rect(x + 0.5, y + 0.5, 3, 3, pos_color)
                elif self.positioning_point_type in ("circle", "rounded"):
                    cx = border * box_size + (x + 0.5) * box_size
                    cy = border * box_size + (y + 0.5) * box_size
                    draw.ellipse(
                        [
                            cx - 1.5 * box_size,
                            cy - 1.5 * box_size,
                            cx + 1.5 * box_size,
                            cy + 1.5 * box_size,
                        ],
                        fill=pos_color,
                        outline=None,
                    )

        # Data/alignment/timing: lines and dots
        line_type = self.content_line_type
        for y in range(n):
            for x in range(n):
                if not table[y][x]:
                    continue
                pt = type_table[y][x]
                if pt == QRPointType.POS_CENTER or pt == QRPointType.POS_OTHER:
                    continue

                if line_type == "horizontal":
                    if x == 0 or (x > 0 and (not table[y][x - 1] or not ava2[y][x - 1])):
                        end = x
                        while end < n and table[y][end] and ava2[y][end]:
                            end += 1
                        if end - x > 1:
                            for i in range(x, end):
                                ava2[y][i] = available[y][i] = False
                            draw_line(x + 0.5, y + 0.5, end - 0.5, y + 0.5, size, color)
                    if available[y][x]:
                        fill_rect(x + 0.5, y + 0.5, size, size, color)

                elif line_type == "vertical":
                    if y == 0 or (y > 0 and (not table[y - 1][x] or not ava2[y - 1][x])):
                        end = y
                        while end < n and table[end][x] and ava2[end][x]:
                            end += 1
                        if end - y > 1:
                            for i in range(y, end):
                                ava2[i][x] = available[i][x] = False
                            draw_line(x + 0.5, y + 0.5, x + 0.5, end - 1 + 0.5, size, color)
                    if available[y][x]:
                        fill_rect(x + 0.5, y + 0.5, size, size, color)

                elif line_type == "interlock":
                    # vertical run
                    if y == 0 or (y > 0 and (not table[y - 1][x] or not ava2[y - 1][x])):
                        end = y
                        while end < n and table[end][x] and ava2[end][x] and end - y <= 3:
                            end += 1
                        if end - y > 1:
                            for i in range(y, end):
                                ava2[i][x] = available[i][x] = False
                            draw_line(x + 0.5, y + 0.5, x + 0.5, end - 1 + 0.5, size, color)
                    # horizontal run
                    if x == 0 or (x > 0 and (not table[y][x - 1] or not ava2[y][x - 1])):
                        end = x
                        while end < n and table[y][end] and ava2[y][end] and end - x <= 3:
                            end += 1
                        if end - x > 1:
                            for i in range(x, end):
                                ava2[y][i] = available[y][i] = False
                            draw_line(x + 0.5, y + 0.5, end - 0.5, y + 0.5, size, color)
                    if available[y][x]:
                        fill_rect(x + 0.5, y + 0.5, size, size, color)

                else:
                    # default: dot only
                    if available[y][x]:
                        fill_rect(x + 0.5, y + 0.5, size, size, color)

    def save(self, stream, format=None, **kwargs):
        if format is None:
            format = self.kind
        self._img.save(stream, format=format, **kwargs)

    def __getattr__(self, name):
        return getattr(self._img, name)

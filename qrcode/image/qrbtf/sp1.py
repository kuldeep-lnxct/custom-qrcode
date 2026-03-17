"""
SP1-style QR: DSJ or square finder, vertical/horizontal bars, X-marks in 2x2/3x3.
Colors: positioning, xmark, content (red), important (yellow) - matching frontend.
"""

from __future__ import annotations

from PIL import Image, ImageDraw

import qrcode.image.base
from qrcode.point_types import QRPointType, get_type_table


class SP1StyledPilImage(qrcode.image.base.BaseImage):
    """Renders QR with SP1 style: DSJ finder, bars, X-marks."""

    kind = "PNG"
    needs_drawrect = False
    needs_processing = True

    # Frontend default colors
    POS_COLOR = (11, 45, 151)      # #0B2D97
    XMARK_COLOR = (11, 45, 151)   # #0B2D97
    CONTENT_COLOR = (224, 32, 32) # #E02020
    IMPORTANT_COLOR = (246, 181, 6)  # #F6B506

    def __init__(self, *args, **kwargs):
        self.content_stroke_width = kwargs.pop("content_stroke_width", 0.7)
        self.content_x_stroke_width = kwargs.pop("content_x_stroke_width", 0.7)
        self.positioning_stroke_width = kwargs.pop("positioning_stroke_width", 0.9)
        self.positioning_point_type = kwargs.pop("positioning_point_type", "dsj")
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
        pos_w = self.positioning_stroke_width
        c_w = self.content_stroke_width
        x_w = self.content_x_stroke_width

        def px(x, y):
            return (
                border * box_size + x * box_size,
                border * box_size + y * box_size,
            )

        available = [[True] * n for _ in range(n)]
        ava2 = [[True] * n for _ in range(n)]

        # Position finders
        for y in range(n):
            for x in range(n):
                if type_table[y][x] != QRPointType.POS_CENTER or not table[y][x]:
                    continue
                if self.positioning_point_type == "square":
                    x0, y0 = px(x - 1.5, y - 1.5)
                    draw.rectangle(
                        [x0, y0, x0 + 3 * box_size, y0 + 3 * box_size],
                        fill=self.POS_COLOR,
                        outline=self.POS_COLOR,
                        width=1,
                    )
                    x0, y0 = px(x - 3, y - 3)
                    draw.rectangle(
                        [x0, y0, x0 + 6 * box_size, y0 + 6 * box_size],
                        fill=None,
                        outline=self.POS_COLOR,
                        width=1,
                    )
                elif self.positioning_point_type == "dsj":
                    off = (1 - pos_w) / 2
                    x0, y0 = px(x - 1 + off, y - 1 + off)
                    draw.rectangle(
                        [
                            x0,
                            y0,
                            x0 + (3 - (1 - pos_w)) * box_size,
                            y0 + (3 - (1 - pos_w)) * box_size,
                        ],
                        fill=self.POS_COLOR,
                    )
                    for (dx, dy, w, h) in [
                        (-3, -1, pos_w, 3 - (1 - pos_w)),
                        (3, -1, pos_w, 3 - (1 - pos_w)),
                        (-1, -3, 3 - (1 - pos_w), pos_w),
                        (-1, 3, 3 - (1 - pos_w), pos_w),
                    ]:
                        x0, y0 = px(x + dx + off, y + dy + off)
                        draw.rectangle(
                            [
                                x0,
                                y0,
                                x0 + w * box_size,
                                y0 + h * box_size,
                            ],
                            fill=self.POS_COLOR,
                        )

        # X-marks in 3x3 and 2x2 blocks, then vertical/horizontal bars, then dots
        for y in range(n):
            for x in range(n):
                if not table[y][x]:
                    continue
                pt = type_table[y][x]
                if pt in (QRPointType.POS_CENTER, QRPointType.POS_OTHER):
                    continue

                # 3x3 X
                if (
                    available[y][x]
                    and ava2[y][x]
                    and x <= n - 3
                    and y <= n - 3
                    and all(ava2[y + i][x + j] for i in range(3) for j in range(3))
                    and table[y + 2][x]
                    and table[y + 1][x + 1]
                    and table[y][x + 2]
                    and table[y + 2][x + 2]
                ):
                    x0, y0 = px(x, y)
                    x1, y1 = px(x + 3, y + 3)
                    margin = x_w / (2**0.5) * box_size
                    draw.line(
                        [x0 + margin, y0 + margin, x1 - margin, y1 - margin],
                        fill=self.XMARK_COLOR,
                        width=max(1, int(x_w * box_size)),
                    )
                    draw.line(
                        [x1 - margin, y0 + margin, x0 + margin, y1 - margin],
                        fill=self.XMARK_COLOR,
                        width=max(1, int(x_w * box_size)),
                    )
                    for i in range(3):
                        for j in range(3):
                            available[y + i][x + j] = ava2[y + i][x + j] = False

                # 2x2 X
                if (
                    available[y][x]
                    and ava2[y][x]
                    and x <= n - 2
                    and y <= n - 2
                    and all(ava2[y + i][x + j] for i in range(2) for j in range(2))
                    and table[y + 1][x]
                    and table[y][x + 1]
                    and table[y + 1][x + 1]
                ):
                    x0, y0 = px(x, y)
                    x1, y1 = px(x + 2, y + 2)
                    margin = x_w / (2**0.5) * box_size
                    draw.line(
                        [x0 + margin, y0 + margin, x1 - margin, y1 - margin],
                        fill=self.XMARK_COLOR,
                        width=max(1, int(x_w * box_size)),
                    )
                    draw.line(
                        [x1 - margin, y0 + margin, x0 + margin, y1 - margin],
                        fill=self.XMARK_COLOR,
                        width=max(1, int(x_w * box_size)),
                    )
                    for i in range(2):
                        for j in range(2):
                            available[y + i][x + j] = ava2[y + i][x + j] = False

        # Vertical bars
        for y in range(n):
            for x in range(n):
                if not (available[y][x] and ava2[y][x]):
                    continue
                if not table[y][x]:
                    continue
                if y == 0 or (y > 0 and (not table[y - 1][x] or not ava2[y - 1][x])):
                    end = y
                    while end < n and table[end][x] and ava2[end][x]:
                        end += 1
                    if end - y > 2:
                        for i in range(y, end):
                            ava2[i][x] = available[i][x] = False
                        x0, y0 = px(x + (1 - c_w) / 2, y + (1 - c_w) / 2)
                        draw.rectangle(
                            [
                                x0,
                                y0,
                                x0 + c_w * box_size,
                                y0 + (end - y - 1 - (1 - c_w)) * box_size,
                            ],
                            fill=self.CONTENT_COLOR,
                        )
                        x0, y0 = px(x + (1 - c_w) / 2, end - 1 + (1 - c_w) / 2)
                        draw.rectangle(
                            [
                                x0,
                                y0,
                                x0 + c_w * box_size,
                                y0 + c_w * box_size,
                            ],
                            fill=self.CONTENT_COLOR,
                        )

        # Horizontal bars (important color)
        for y in range(n):
            for x in range(n):
                if not (available[y][x] and ava2[y][x]):
                    continue
                if not table[y][x]:
                    continue
                if x == 0 or (x > 0 and (not table[y][x - 1] or not ava2[y][x - 1])):
                    end = x
                    while end < n and table[y][end] and ava2[y][end]:
                        end += 1
                    if end - x > 1:
                        for i in range(x, end):
                            ava2[y][i] = available[y][i] = False
                        x0, y0 = px(x + (1 - c_w) / 2, y + (1 - c_w) / 2)
                        draw.rectangle(
                            [
                                x0,
                                y0,
                                x0 + (end - x - (1 - c_w)) * box_size,
                                y0 + c_w * box_size,
                            ],
                            fill=self.IMPORTANT_COLOR,
                        )

        # Single dots
        for y in range(n):
            for x in range(n):
                if not available[y][x]:
                    continue
                if not table[y][x]:
                    continue
                pt = type_table[y][x]
                if pt in (QRPointType.POS_CENTER, QRPointType.POS_OTHER):
                    continue
                x0, y0 = px(x + (1 - c_w) / 2, y + (1 - c_w) / 2)
                draw.rectangle(
                    [
                        x0,
                        y0,
                        x0 + c_w * box_size,
                        y0 + c_w * box_size,
                    ],
                    fill=self.IMPORTANT_COLOR,
                )

    def save(self, stream, format=None, **kwargs):
        if format is None:
            format = self.kind
        self._img.save(stream, format=format, **kwargs)

    def __getattr__(self, name):
        return getattr(self._img, name)

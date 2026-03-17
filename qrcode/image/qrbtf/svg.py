"""
SVG output for qrbtf styles (A1, A2, SP1).

Produces vector SVG matching the frontend viewBox and shapes.
C2 is image-based and is not supported in SVG (use PNG).
Optional background image is embedded as data URI so the SVG is self-contained.
"""

from __future__ import annotations

import base64
import mimetypes
from io import BytesIO
from pathlib import Path
from typing import Any

from qrcode.compat.etree import ET
from qrcode.image.base import BaseImage
from qrcode.point_types import QRPointType, get_type_table

# Rounded square path (sq25 from frontend constants), in 0..100 coords
SQ25_PATH = (
    "M32.048565,-1.29480038e-15 L67.951435,1.29480038e-15 "
    "C79.0954192,-7.52316311e-16 83.1364972,1.16032014 87.2105713,3.3391588 "
    "C91.2846454,5.51799746 94.4820025,8.71535463 96.6608412,12.7894287 "
    "C98.8396799,16.8635028 100,20.9045808 100,32.048565 L100,67.951435 "
    "C100,79.0954192 98.8396799,83.1364972 96.6608412,87.2105713 "
    "C94.4820025,91.2846454 91.2846454,94.4820025 87.2105713,96.6608412 "
    "C83.1364972,98.8396799 79.0954192,100 67.951435,100 L32.048565,100 "
    "C20.9045808,100 16.8635028,98.8396799 12.7894287,96.6608412 "
    "C8.71535463,94.4820025 5.51799746,91.2846454 3.3391588,87.2105713 "
    "C1.16032014,83.1364972 0,79.0954192 0,67.951435 L0,32.048565 "
    "C0,20.9045808 1.16032014,16.8635028 3.3391588,12.7894287 "
    "C5.51799746,8.71535463 8.71535463,5.51799746 12.7894287,3.3391588 "
    "C16.8635028,1.16032014 20.9045808,0 32.048565,0 Z"
)


def _el(tag: str, **attrs: Any) -> ET.Element:
    """Create an SVG element with local name (no namespace prefix)."""
    return ET.Element(
        tag, **{k: str(v) for k, v in attrs.items() if v is not None}
    )


def _image_to_data_uri(path: str | None = None, image=None) -> str | None:
    """Return a data URI for the given file path or PIL Image, or None."""
    if path:
        p = Path(path)
        if not p.exists():
            return None
        mime, _ = mimetypes.guess_type(str(p))
        mime = mime or "image/png"
        data = p.read_bytes()
    elif image is not None:
        from PIL import Image

        buf = BytesIO()
        if not isinstance(image, Image.Image):
            image = Image.open(image)
        fmt = (image.format or "PNG").upper()
        if fmt == "JPEG":
            mime = "image/jpeg"
            image.convert("RGB").save(buf, format="JPEG")
        else:
            mime = "image/png"
            image.convert("RGBA").save(buf, format="PNG")
        data = buf.getvalue()
    else:
        return None
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{b64}"


class QrbtfSvgImage(BaseImage):
    """Base for qrbtf SVG images: builds SVG in process() from modules and type_table."""

    kind = "SVG"
    allowed_kinds = ("SVG",)
    needs_drawrect = False
    needs_processing = True
    _svg_ns = "http://www.w3.org/2000/svg"

    def __init__(self, *args, **kwargs):
        self.background_path = kwargs.pop("background_path", None)
        self.background_image = kwargs.pop("background_image", None)
        self.logo_path = kwargs.pop("logo_path", None)
        self.logo_image = kwargs.pop("logo_image", None)
        self.logo_size = float(kwargs.pop("logo_size", 8))
        self.logo_margin = float(kwargs.pop("logo_margin", 1))
        self.text = kwargs.pop("text", None)
        self.text_position = kwargs.pop("text_position", "bottom")
        self.text_color = kwargs.pop("text_color", "#000000")
        text_fs = kwargs.pop("text_font_size", None)
        self.text_font_size = float(text_fs) if text_fs is not None else None
        svg_margin = kwargs.pop("svg_margin", None)
        self.svg_margin = float(svg_margin) if svg_margin is not None else None
        super().__init__(*args, **kwargs)

    def new_image(self, **kwargs):
        n = self.width
        margin = self.svg_margin if self.svg_margin is not None else n / 5
        size = n + 2 * margin
        view_box = f"{-margin} {-margin} {size} {size}"
        # Use local name "svg" and set xmlns so default namespace applies to all children
        svg = ET.Element(
            "svg",
            xmlns=self._svg_ns,
            viewBox=view_box,
            width=f"{self.pixel_size}",
            height=f"{self.pixel_size}",
        )
        # Background image (center-fill of viewBox), embedded as data URI
        href = _image_to_data_uri(self.background_path, self.background_image)
        if href:
            img_el = ET.Element(
                "image",
                x=str(-margin),
                y=str(-margin),
                width=str(size),
                height=str(size),
                href=href,
                preserveAspectRatio="xMidYMid slice",
            )
            svg.insert(0, img_el)
        return svg

    def drawrect(self, row, col):
        pass

    def _has_logo(self):
        """True if a center logo will be drawn (logo_path or logo_image set)."""
        return bool(self.logo_path or self.logo_image)

    def _in_logo_zone(self, row: int, col: int) -> bool:
        """True if (row, col) is inside the logo area plus margin; no QR content drawn there."""
        if not self._has_logo():
            return False
        n = self.width
        s = self.logo_size
        margin = self.logo_margin
        half = s / 2 + margin
        cx = cy = n / 2
        x, y = col + 0.5, row + 0.5
        return (cx - half <= x <= cx + half) and (cy - half <= y <= cy + half)

    def _add_center_logo(self):
        """Append a center logo image on top of the QR (overlay). Uses logo_path or logo_image.
        No QR content is drawn in the logo zone (see _in_logo_zone); background there stays transparent."""
        href = _image_to_data_uri(self.logo_path, self.logo_image)
        if not href:
            return
        n = self.width
        s = self.logo_size
        x = n / 2 - s / 2
        y = n / 2 - s / 2
        img_el = ET.Element(
            "image",
            x=str(x),
            y=str(y),
            width=str(s),
            height=str(s),
            href=href,
            preserveAspectRatio="xMidYMid meet",
        )
        self._img.append(img_el)

    def _add_side_text(self):
        """Append optional text on one side of the QR (top, bottom, left, right)."""
        if not self.text:
            return
        n = self.width
        margin = self.svg_margin if self.svg_margin is not None else n / 5
        pos = (self.text_position or "bottom").lower()
        fs = self.text_font_size if self.text_font_size is not None else max(1.5, n / 5)
        text_el = ET.Element("text", fill=self.text_color)
        text_el.set("text-anchor", "middle")
        text_el.set("font-size", str(fs))
        text_el.set("style", "font-family: sans-serif; font-weight: normal;")
        text_el.text = self.text
        if pos == "top":
            text_el.set("x", str(n / 2))
            text_el.set("y", str(-margin / 2))
            text_el.set("dominant-baseline", "middle")
            self._img.append(text_el)
        elif pos == "bottom":
            text_el.set("x", str(n / 2))
            text_el.set("y", str(n + margin / 2))
            text_el.set("dominant-baseline", "middle")
            self._img.append(text_el)
        elif pos == "left":
            text_el.set("x", str(-margin / 2))
            text_el.set("y", str(n / 2))
            text_el.set("dominant-baseline", "middle")
            text_el.set("transform", f"rotate(-90, {-margin/2}, {n/2})")
            self._img.append(text_el)
        elif pos == "right":
            text_el.set("x", str(n + margin / 2))
            text_el.set("y", str(n / 2))
            text_el.set("dominant-baseline", "middle")
            text_el.set("transform", f"rotate(90, {n + margin/2}, {n/2})")
            self._img.append(text_el)
        else:
            # fallback: bottom
            text_el.set("x", str(n / 2))
            text_el.set("y", str(n + margin / 2))
            text_el.set("dominant-baseline", "middle")
            self._img.append(text_el)

    def save(self, stream, kind=None, **kwargs):
        if kind is not None:
            self.check_kind(kind=kind)
        ET.ElementTree(self._img).write(
            stream, encoding="UTF-8", xml_declaration=True
        )

    def __getattr__(self, name):
        return getattr(self._img, name)


def _normalize_opts(kwargs: dict) -> None:
    """Replace hyphen keys with underscore so options from CLI/API match."""
    for k in list(kwargs):
        if "-" in k:
            kwargs[k.replace("-", "_")] = kwargs.pop(k)


class A1SvgImage(QrbtfSvgImage):
    """A1-style QR as SVG: square/circle/planet/rounded finders, scalable content."""

    def __init__(self, *args, **kwargs):
        _normalize_opts(kwargs)
        self.positioning_point_type = kwargs.pop("positioning_point_type", "square")
        self.content_point_type = kwargs.pop("content_point_type", "square")
        self.content_point_scale = kwargs.pop("content_point_scale", 1.0)
        self.content_point_opacity = kwargs.pop("content_point_opacity", 1.0)
        self.content_point_color = kwargs.pop("content_point_color", "#000000")
        self.positioning_point_color = kwargs.pop("positioning_point_color", "#000000")
        super().__init__(*args, **kwargs)

    def process(self):
        n = self.width
        table = self.modules
        type_table = get_type_table(n)
        scale = self.content_point_scale * 1.01
        scale_half = scale / 2
        offset = (1 - scale) / 2
        pos_type = self.positioning_point_type
        content_type = self.content_point_type
        pos_color = self.positioning_point_color
        content_color = self.content_point_color
        opacity = self.content_point_opacity

        for row in range(n):
            for col in range(n):
                if not table[row][col]:
                    continue
                if self._in_logo_zone(row, col):
                    continue
                pt = type_table[row][col]
                x, y = col + 0.5, row + 0.5

                if pt == QRPointType.POS_CENTER:
                    if pos_type == "square":
                        self._img.append(
                            _el(
                                "rect",
                                x=x - 1.5,
                                y=y - 1.5,
                                width=3,
                                height=3,
                                fill=pos_color,
                            )
                        )
                        self._img.append(
                            _el(
                                "rect",
                                x=x - 3,
                                y=y - 3,
                                width=6,
                                height=6,
                                fill="none",
                                stroke=pos_color,
                                stroke_width="1",
                            )
                        )
                    elif pos_type in ("circle", "planet"):
                        self._img.append(
                            _el("circle", cx=x, cy=y, r=1.5, fill=pos_color)
                        )
                        dash = "0.5,0.5" if pos_type == "planet" else None
                        self._img.append(
                            _el(
                                "circle",
                                cx=x,
                                cy=y,
                                r=3,
                                fill="none",
                                stroke=pos_color,
                                stroke_width="0.15" if pos_type == "planet" else "1",
                                stroke_dasharray=dash,
                            )
                        )
                        if pos_type == "planet":
                            for dx, dy in [(3, 0), (-3, 0), (0, 3), (0, -3)]:
                                self._img.append(
                                    _el("circle", cx=x + dx, cy=y + dy, r=0.5, fill=pos_color)
                                )
                    elif pos_type == "rounded":
                        self._img.append(
                            _el("circle", cx=x, cy=y, r=1.5, fill=pos_color)
                        )
                        # sq25 path scaled to 6x6 at (x-3, y-3)
                        path = ET.SubElement(self._img, "path")
                        path.set("d", SQ25_PATH)
                        path.set("stroke", pos_color)
                        path.set("fill", "none")
                        path.set("stroke-width", str((100 / 6) * (1 - (1 - scale) * 0.75)))
                        path.set(
                            "transform",
                            f"translate({x - 3},{y - 3}) scale(0.06,0.06)",
                        )
                    continue
                if pt in (QRPointType.POS_OTHER,):
                    continue

                # Data/alignment/timing
                if content_type == "square":
                    sz = scale
                    off = offset
                else:
                    sz = scale_half
                    off = (1 - scale) / 2
                opts = {"fill": content_color, "opacity": str(opacity)}
                if content_type == "square":
                    self._img.append(
                        _el(
                            "rect",
                            x=x - 0.5 + off,
                            y=y - 0.5 + off,
                            width=sz,
                            height=sz,
                            **opts,
                        )
                    )
                else:
                    self._img.append(
                        _el("circle", cx=x, cy=y, r=sz, **opts)
                    )
        self._add_center_logo()
        self._add_side_text()


class A2SvgImage(QrbtfSvgImage):
    """A2-style QR as SVG: line-based content (horizontal, vertical, interlock, etc.)."""

    def __init__(self, *args, **kwargs):
        _normalize_opts(kwargs)
        self.content_line_type = kwargs.pop("content_line_type", "interlock")
        self.content_point_scale = kwargs.pop("content_point_scale", 0.6)
        self.content_point_opacity = kwargs.pop("content_point_opacity", 1.0)
        self.content_point_color = kwargs.pop("content_point_color", "#000000")
        self.positioning_point_type = kwargs.pop("positioning_point_type", "rounded")
        self.positioning_point_color = kwargs.pop("positioning_point_color", "#000000")
        super().__init__(*args, **kwargs)

    def process(self):
        n = self.width
        table = self.modules
        type_table = get_type_table(n)
        line_type = self.content_line_type
        size = self.content_point_scale
        opacity = self.content_point_opacity
        color = self.content_point_color
        pos_color = self.positioning_point_color
        available = [[True] * n for _ in range(n)]
        ava2 = [[True] * n for _ in range(n)]

        def line(x1, y1, x2, y2):
            self._img.append(
                _el(
                    "line",
                    x1=x1,
                    y1=y1,
                    x2=x2,
                    y2=y2,
                    stroke=color,
                    stroke_width=str(size),
                    stroke_linecap="round",
                    opacity=str(opacity),
                )
            )

        def circle(x, y, r):
            self._img.append(
                _el("circle", cx=x, cy=y, r=r, fill=color, opacity=str(opacity))
            )

        # Finders
        for row in range(n):
            for col in range(n):
                if type_table[row][col] != QRPointType.POS_CENTER or not table[row][col]:
                    continue
                if self._in_logo_zone(row, col):
                    continue
                x, y = col + 0.5, row + 0.5
                if self.positioning_point_type == "square":
                    self._img.append(
                        _el("rect", x=x - 1.5, y=y - 1.5, width=3, height=3, fill=pos_color)
                    )
                    self._img.append(
                        _el(
                            "rect",
                            x=x - 3,
                            y=y - 3,
                            width=6,
                            height=6,
                            fill="none",
                            stroke=pos_color,
                            stroke_width="1",
                        )
                    )
                else:
                    self._img.append(_el("circle", cx=x, cy=y, r=1.5, fill=pos_color))
                    self._img.append(
                        _el(
                            "circle",
                            cx=x,
                            cy=y,
                            r=3,
                            fill="none",
                            stroke=pos_color,
                            stroke_width="1",
                        )
                    )

        # Lines and dots (simplified: interlock-style runs)
        for row in range(n):
            for col in range(n):
                if not table[row][col]:
                    continue
                if self._in_logo_zone(row, col):
                    continue
                pt = type_table[row][col]
                if pt in (QRPointType.POS_CENTER, QRPointType.POS_OTHER):
                    continue
                x, y = col + 0.5, row + 0.5
                if line_type == "horizontal":
                    if col == 0 or not table[row][col - 1] or not ava2[row][col - 1]:
                        end = col
                        while end < n and table[row][end] and ava2[row][end]:
                            end += 1
                        if end - col > 1:
                            for i in range(col, end):
                                ava2[row][i] = available[row][i] = False
                            line(x, y, end - 0.5, y)
                    if available[row][col]:
                        circle(x, y, size / 2)
                elif line_type == "vertical":
                    if row == 0 or not table[row - 1][col] or not ava2[row - 1][col]:
                        end = row
                        while end < n and table[end][col] and ava2[end][col]:
                            end += 1
                        if end - row > 1:
                            for i in range(row, end):
                                ava2[i][col] = available[i][col] = False
                            line(x, y, x, end - 1 + 0.5)
                    if available[row][col]:
                        circle(x, y, size / 2)
                else:
                    if available[row][col]:
                        circle(x, y, size / 2)
        self._add_center_logo()
        self._add_side_text()


class SP1SvgImage(QrbtfSvgImage):
    """SP1-style QR as SVG: DSJ finder, bars, X-marks."""

    POS_COLOR = "#0B2D97"
    XMARK_COLOR = "#0B2D97"
    CONTENT_COLOR = "#E02020"
    IMPORTANT_COLOR = "#F6B506"

    def __init__(self, *args, **kwargs):
        _normalize_opts(kwargs)
        self.content_stroke_width = kwargs.pop("content_stroke_width", 0.7)
        self.content_x_stroke_width = kwargs.pop("content_x_stroke_width", 0.7)
        self.positioning_stroke_width = kwargs.pop("positioning_stroke_width", 0.9)
        self.positioning_point_type = kwargs.pop("positioning_point_type", "dsj")
        super().__init__(*args, **kwargs)

    def process(self):
        n = self.width
        table = self.modules
        type_table = get_type_table(n)
        pos_w = self.positioning_stroke_width
        c_w = self.content_stroke_width
        x_w = self.content_x_stroke_width
        available = [[True] * n for _ in range(n)]
        ava2 = [[True] * n for _ in range(n)]

        for row in range(n):
            for col in range(n):
                if not table[row][col]:
                    continue
                if self._in_logo_zone(row, col):
                    continue
                pt = type_table[row][col]
                x, y = col, row
                if pt == QRPointType.POS_CENTER:
                    if self.positioning_point_type == "square":
                        self._img.append(
                            _el(
                                "rect",
                                x=x - 1.5,
                                y=y - 1.5,
                                width=3,
                                height=3,
                                fill=self.POS_COLOR,
                            )
                        )
                        self._img.append(
                            _el(
                                "rect",
                                x=x - 3,
                                y=y - 3,
                                width=6,
                                height=6,
                                fill="none",
                                stroke=self.POS_COLOR,
                                stroke_width="1",
                            )
                        )
                    else:
                        off = (1 - pos_w) / 2
                        self._img.append(
                            _el(
                                "rect",
                                x=x - 1 + off,
                                y=y - 1 + off,
                                width=3 - (1 - pos_w),
                                height=3 - (1 - pos_w),
                                fill=self.POS_COLOR,
                            )
                        )
                        for dx, dy, w, h in [
                            (-3, -1, pos_w, 3 - (1 - pos_w)),
                            (3, -1, pos_w, 3 - (1 - pos_w)),
                            (-1, -3, 3 - (1 - pos_w), pos_w),
                            (-1, 3, 3 - (1 - pos_w), pos_w),
                        ]:
                            self._img.append(
                                _el(
                                    "rect",
                                    x=x + dx + off,
                                    y=y + dy + off,
                                    width=w,
                                    height=h,
                                    fill=self.POS_COLOR,
                                )
                            )
                    continue
                if pt == QRPointType.POS_OTHER:
                    continue

                if self._in_logo_zone(row, col):
                    continue
                # 3x3 X
                if (
                    available[row][col]
                    and ava2[row][col]
                    and col <= n - 3
                    and row <= n - 3
                    and all(ava2[row + i][col + j] for i in range(3) for j in range(3))
                    and table[row + 2][col]
                    and table[row + 1][col + 1]
                    and table[row][col + 2]
                    and table[row + 2][col + 2]
                ):
                    m = x_w / (2**0.5)
                    self._img.append(
                        _el(
                            "line",
                            x1=col + m,
                            y1=row + m,
                            x2=col + 3 - m,
                            y2=row + 3 - m,
                            stroke=self.XMARK_COLOR,
                            stroke_width=str(x_w),
                        )
                    )
                    self._img.append(
                        _el(
                            "line",
                            x1=col + 3 - m,
                            y1=row + m,
                            x2=col + m,
                            y2=row + 3 - m,
                            stroke=self.XMARK_COLOR,
                            stroke_width=str(x_w),
                        )
                    )
                    for i in range(3):
                        for j in range(3):
                            available[row + i][col + j] = ava2[row + i][col + j] = False
                # 2x2 X
                elif (
                    available[row][col]
                    and ava2[row][col]
                    and col <= n - 2
                    and row <= n - 2
                    and all(ava2[row + i][col + j] for i in range(2) for j in range(2))
                    and table[row + 1][col]
                    and table[row][col + 1]
                    and table[row + 1][col + 1]
                ):
                    m = x_w / (2**0.5)
                    self._img.append(
                        _el(
                            "line",
                            x1=col + m,
                            y1=row + m,
                            x2=col + 2 - m,
                            y2=row + 2 - m,
                            stroke=self.XMARK_COLOR,
                            stroke_width=str(x_w),
                        )
                    )
                    self._img.append(
                        _el(
                            "line",
                            x1=col + 2 - m,
                            y1=row + m,
                            x2=col + m,
                            y2=row + 2 - m,
                            stroke=self.XMARK_COLOR,
                            stroke_width=str(x_w),
                        )
                    )
                    for i in range(2):
                        for j in range(2):
                            available[row + i][col + j] = ava2[row + i][col + j] = False

        # Vertical bars
        for row in range(n):
            for col in range(n):
                if not (available[row][col] and ava2[row][col] and table[row][col]):
                    continue
                if self._in_logo_zone(row, col):
                    continue
                if row == 0 or not table[row - 1][col] or not ava2[row - 1][col]:
                    end = row
                    while end < n and table[end][col] and ava2[end][col]:
                        end += 1
                    if end - row > 2:
                        for i in range(row, end):
                            ava2[i][col] = available[i][col] = False
                        off = (1 - c_w) / 2
                        self._img.append(
                            _el(
                                "rect",
                                x=col + off,
                                y=row + off,
                                width=c_w,
                                height=end - row - 1 - (1 - c_w),
                                fill=self.CONTENT_COLOR,
                            )
                        )
                        self._img.append(
                            _el(
                                "rect",
                                x=col + off,
                                y=end - 1 + off,
                                width=c_w,
                                height=c_w,
                                fill=self.CONTENT_COLOR,
                            )
                        )

        # Horizontal bars
        for row in range(n):
            for col in range(n):
                if not (available[row][col] and ava2[row][col] and table[row][col]):
                    continue
                if self._in_logo_zone(row, col):
                    continue
                if col == 0 or not table[row][col - 1] or not ava2[row][col - 1]:
                    end = col
                    while end < n and table[row][end] and ava2[row][end]:
                        end += 1
                    if end - col > 1:
                        for i in range(col, end):
                            ava2[row][i] = available[row][i] = False
                        off = (1 - c_w) / 2
                        self._img.append(
                            _el(
                                "rect",
                                x=col + off,
                                y=row + off,
                                width=end - col - (1 - c_w),
                                height=c_w,
                                fill=self.IMPORTANT_COLOR,
                            )
                        )

        # Dots
        for row in range(n):
            for col in range(n):
                if not available[row][col] or not table[row][col]:
                    continue
                if self._in_logo_zone(row, col):
                    continue
                if type_table[row][col] in (QRPointType.POS_CENTER, QRPointType.POS_OTHER):
                    continue
                off = (1 - c_w) / 2
                self._img.append(
                    _el(
                        "rect",
                        x=col + off,
                        y=row + off,
                        width=c_w,
                        height=c_w,
                        fill=self.IMPORTANT_COLOR,
                    )
                )
        self._add_center_logo()
        self._add_side_text()
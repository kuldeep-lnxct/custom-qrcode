# Qrbtf-style QR codes

This package provides the same visual styles as the [qrbtf](https://github.com/qrbtf/qrbtf) frontend library, so you can generate styled QR codes in Python (e.g. for PNG/SVG export or server-side rendering).

## Styles and presets

| Style | Description | Presets |
|-------|-------------|---------|
| **A1** | Square/circle/planet/rounded finders, scalable content (square or circle modules) | `a1`, `a1c`, `a1p` |
| **A2** | Line-based content (horizontal, vertical, interlock) with dots | `a2`, `a2c` |
| **C2** | Image background with contrast/brightness dithering; finder = big (B), data = small (S) | — |
| **SP1** | DSJ or square finder; vertical/horizontal bars; X-marks in 2×2 and 3×3 blocks | `sp1` |

## Command line (presets and options)

Use the `qr` script with `--style=PRESET` to pick a preset. Override any option with `--opt KEY=VALUE` (or `-O`); repeat for multiple options.

**SVG output:** Use an output path ending in `.svg` to get vector SVG (A1, A2, SP1 only; C2 is image-based and outputs PNG only). You can add a full **background image** with `-O background_path=...`, a **center logo** with `-O logo_path=...`, or **side text** with `-O text=...` and `-O text_position=top|bottom|left|right`:

```bash
qr --style=a1c "https://example.com" -o qr_a1c.svg
qr --style=a1 -O background_path=photo.jpg -o qr.svg "https://example.com"
qr --style=a1 -O logo_path=logo.png -O logo_size=8 -o qr.svg "https://example.com"
qr --style=a1 -o qr.svg -O "text=Scan me" -O text_position=bottom "https://example.com"
qr --style=a2 "https://example.com" -o qr_a2.svg
qr --style=sp1 "https://example.com" -o qr_sp1.svg
```

**Presets:**

```bash
# A1 presets: a1 (square), a1c (circle, scaled), a1p (planet finder)
qr --style=a1 "https://example.com" -o qr_a1.png
qr --style=a1c "https://example.com" -o qr_a1c.png
qr --style=a1p "https://example.com" -o qr_a1p.png

# A2 presets: a2 (interlock), a2c (cross)
qr --style=a2 "https://example.com" -o qr_a2.png
qr --style=a2c "https://example.com" -o qr_a2c.png

# SP1, C2
qr --style=sp1 "https://example.com" -o qr_sp1.png
qr --style=c2 "https://example.com" -o qr_c2.png
```

**Overriding options with `--opt` / `-O`:**

```bash
# A1: circle finder, circle modules, 50% scale, custom color
qr --style=a1 -O positioning_point_type=circle -O content_point_type=circle -O content_point_scale=0.5 -o qr.png "https://example.com"

# A1: rounded finder, blue content color
qr --style=a1c -O positioning_point_type=rounded -O content_point_color=#0000ff -o qr.png "https://example.com"

# A2: horizontal lines, 80% stroke scale
qr --style=a2 -O content_line_type=horizontal -O content_point_scale=0.8 -o qr.png "https://example.com"

# SP1: square finder, stroke widths
qr --style=sp1 -O positioning_point_type=square -O content_stroke_width=0.8 -o qr.png "https://example.com"

# C2: background image, contrast and brightness (PNG only; C2 does not support SVG)
qr --style=c2 -O background_path=bg.jpg -O contrast=0.2 -O brightness=0.1 -o qr.png "https://example.com"
```

**Option reference (by style):**

| Style | Option | Values / notes |
|-------|--------|----------------|
| A1 | `positioning_point_type` | `square`, `circle`, `planet`, `rounded` |
| A1 | `content_point_type` | `square`, `circle` |
| A1 | `content_point_scale` | 0–1 (number) |
| A1 | `content_point_opacity` | 0–1 |
| A1 | `content_point_color`, `positioning_point_color` | Hex, e.g. `#000000` |
| A1 | `correct_level` | `L`, `M`, `Q`, `H` |
| A1, A2, SP1 (SVG) | `background_path` | Path to image file; embedded in SVG and centered (cover) |
| A1, A2, SP1 (SVG) | `logo_path` | Path to logo image; embedded and drawn in the **center** of the QR (overlay) |
| A1, A2, SP1 (SVG) | `logo_size` | Size of center logo in module units (default 8); e.g. 7–9 |
| A1, A2, SP1 (SVG) | `logo_margin` | Extra clear margin in module units around the logo (default 1); no QR content is drawn in this zone |
| A1, A2, SP1 (SVG) | `text` | Optional label text (e.g. "Scan me"); use with `text_position` |
| A1, A2, SP1 (SVG) | `text_position` | Where to place text: `top`, `bottom`, `left`, `right` (default `bottom`) |
| A1, A2, SP1 (SVG) | `text_color`, `text_font_size` | Text fill color (hex) and size in viewBox units (optional) |
| A1, A2, SP1 (SVG) | `svg_margin` | Margin (quiet zone) around the QR in module units; default is width/5. Use 0 or 1 for a tighter crop |
| A2 | `content_line_type` | `horizontal`, `vertical`, `interlock`, `radial`, `tl-br`, `tr-bl`, `cross` |
| A2 | `content_point_scale`, `content_point_opacity`, colors | Same as A1 |
| C2 | `background_path` | Path to image file (center-cropped to square if not square) |
| C2 | `contrast`, `brightness` | Numbers (e.g. -1 to 1) |
| C2 | `align_type`, `timing_type` | `none`, `black-white` |
| SP1 | `positioning_point_type` | `dsj`, `square` |
| SP1 | `content_stroke_width`, `content_x_stroke_width`, `positioning_stroke_width` | 0–1 |

Numeric options can be given as integers or decimals (e.g. `0.5`). Colors are hex strings. Use `--error-correction=L|M|Q|H` for error level, or `--opt correct_level=M`.

## Python usage

```python
from qrcode.image.qrbtf import make_qrbtf_a1, make_qrbtf_a2, make_qrbtf_c2, make_qrbtf_sp1

# A1 (default preset "a1": square finder, square modules)
img = make_qrbtf_a1("https://example.com")
img.save("qr_a1.png")

# A1 with preset "a1c" (circle finder, circle modules, scaled)
img = make_qrbtf_a1("https://example.com", preset="a1c")
img.save("qr_a1c.png")

# A2 (interlock lines + dots)
img = make_qrbtf_a2("https://example.com", preset="a2")
img.save("qr_a2.png")

# C2 (image background; use ERROR_CORRECT_H)
img = make_qrbtf_c2(
    "https://example.com",
    background_path="background.jpg",
    contrast=0.2,
    brightness=0.0,
)
img.save("qr_c2.png")

# SP1 (DSJ finder, bars, X-marks)
img = make_qrbtf_sp1("https://example.com", preset="sp1")
img.save("qr_sp1.png")

# SVG with center logo (A1, A2, SP1)
from qrcode.image.qrbtf.styles import make_qrbtf_a1_svg
img = make_qrbtf_a1_svg("https://example.com", logo_path="logo.png", logo_size=8)
img.save("qr_logo.svg")

# SVG with side text (top, bottom, left, right)
img = make_qrbtf_a1_svg("https://example.com", text="Scan me", text_position="bottom")
img.save("qr_text.svg")
```

## Options (matching frontend)

- **A1**: `positioning_point_type` (square | circle | planet | rounded), `content_point_type` (square | circle), `content_point_scale`, `content_point_opacity`, `content_point_color`, `positioning_point_color`, `correct_level`
- **A2**: `content_line_type` (horizontal | vertical | interlock | …), `content_point_scale`, `content_point_opacity`, `content_point_color`, `positioning_point_type`, `positioning_point_color`
- **C2**: `background_image` or `background_path`, `contrast`, `brightness`, `align_type`, `timing_type`
- **SP1**: `content_stroke_width`, `content_x_stroke_width`, `positioning_stroke_width`, `positioning_point_type` (dsj | square)

## Point types

The library adds a small point-type system so drawers can tell finder, alignment, timing, and data modules apart (same as the frontend encoder):

```python
from qrcode import QRCode
from qrcode.point_types import QRPointType, get_type_table

qr = QRCode(box_size=10)
qr.add_data("https://example.com")
qr.make()
tt = get_type_table(qr.modules_count)
# tt[row][col] is QRPointType.DATA, POS_CENTER, POS_OTHER, ALIGN_*, TIMING, etc.
```

Existing module drawers now receive optional `point_type`, `row`, and `col` in `drawrect(box, is_active, point_type=..., row=..., col=...)` for custom finder/data styling.

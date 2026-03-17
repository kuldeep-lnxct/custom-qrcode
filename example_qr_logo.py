#!/usr/bin/env python
"""
Generate the same QR as the CLI command:
  qr --style=a1 --error-correction=H -O content_point_scale=0.8 -O content_point_type=rounded
     -O positioning_point_type=rounded -O content_point_color=#000000
     -O positioning_point_color=#000000 -O logo_path=audio3.png -O logo_size=10
     -O logo_margin=0.5 "https://demo.example.com/qr/subpath/NW94BVCJELRI" -o qr.svg
"""

from qrcode import constants
from qrcode.image.qrbtf.styles import make_qrbtf_a1_svg

DATA = "https://demo.example.com/qr/subpath/NW94BVCJELRI"
OUTPUT = "qr1.svg"

img = make_qrbtf_a1_svg(
    DATA,
    preset="a1",
    box_size=10,
    border=4,
    correct_level=constants.ERROR_CORRECT_H,
    content_point_scale=0.8,
    content_point_type="rounded",
    positioning_point_type="rounded",
    content_point_color="#000000",
    positioning_point_color="#000000",
    logo_path="audio3.png",
    logo_size=10,
    logo_margin=0.5,
    svg_margin=0.5,  # reduce outer margin (default is width/5). Use 0 for minimal margin
)

with open(OUTPUT, "wb") as f:
    img.save(f)

print(f"Saved {OUTPUT}")

#!/usr/bin/env python3
"""Generate assets/icon.png — run once during setup."""
import os
import math
from PIL import Image, ImageDraw

SIZE = 512
OUT = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

BG        = (15,  15,  25)   # near-black
PANEL     = (28,  28,  48)
RED       = (220, 60,  60)
WHITE     = (255, 255, 255)
GRAY      = (140, 140, 160)
GRID_LINE = (50,  50,  75)

img  = Image.new("RGBA", (SIZE, SIZE), BG)
draw = ImageDraw.Draw(img)

# Rounded square background
r = SIZE // 6
draw.rounded_rectangle([0, 0, SIZE - 1, SIZE - 1], radius=r, fill=BG)

# Calendar panel
pad = SIZE // 10
cx, cy = SIZE // 2, SIZE // 2 + SIZE // 20
panel_w = SIZE - 2 * pad
panel_h = int(panel_w * 0.82)
px0 = pad
py0 = cy - panel_h // 2
px1 = px0 + panel_w
py1 = py0 + panel_h
pr  = SIZE // 18
draw.rounded_rectangle([px0, py0, px1, py1], radius=pr, fill=PANEL)

# Header bar
header_h = panel_h // 4
draw.rounded_rectangle([px0, py0, px1, py0 + header_h], radius=pr, fill=RED)
draw.rectangle([px0, py0 + header_h - pr, px1, py0 + header_h], fill=RED)

# Grid lines (3 cols × 2 rows)
cols = 4
rows = 3
cell_w = panel_w // cols
cell_h = (panel_h - header_h) // rows
for c in range(1, cols):
    x = px0 + c * cell_w
    draw.line([(x, py0 + header_h), (x, py1)], fill=GRID_LINE, width=2)
for rr in range(1, rows):
    y = py0 + header_h + rr * cell_h
    draw.line([(px0, y), (px1, y)], fill=GRID_LINE, width=2)

# Dot cells (simulate calendar dates)
dot_r = cell_w // 8
for c in range(cols):
    for rr in range(rows):
        dot_x = px0 + c * cell_w + cell_w // 2
        dot_y = py0 + header_h + rr * cell_h + cell_h // 2
        color = WHITE if not (c == 1 and rr == 0) else RED
        draw.ellipse(
            [dot_x - dot_r, dot_y - dot_r, dot_x + dot_r, dot_y + dot_r],
            fill=color,
        )

# "Ring" binder clips at top
clip_r = SIZE // 22
for cx_clip in [px0 + panel_w // 3, px0 + 2 * panel_w // 3]:
    draw.ellipse(
        [cx_clip - clip_r, py0 - clip_r, cx_clip + clip_r, py0 + clip_r],
        fill=WHITE,
    )
    draw.ellipse(
        [cx_clip - clip_r // 2, py0 - clip_r // 2,
         cx_clip + clip_r // 2, py0 + clip_r // 2],
        fill=BG,
    )

# Alert dot (top-right corner)
alert_cx = px1 - SIZE // 16
alert_cy = py0 - SIZE // 16 + SIZE // 22
alert_r  = SIZE // 14
draw.ellipse(
    [alert_cx - alert_r, alert_cy - alert_r,
     alert_cx + alert_r, alert_cy + alert_r],
    fill=RED,
)
# Exclamation mark
bar_w = max(4, alert_r // 3)
draw.rectangle(
    [alert_cx - bar_w // 2, alert_cy - alert_r // 2,
     alert_cx + bar_w // 2, alert_cy + alert_r // 5],
    fill=WHITE,
)
dot_size = max(3, bar_w // 2)
draw.ellipse(
    [alert_cx - dot_size, alert_cy + alert_r // 3,
     alert_cx + dot_size, alert_cy + alert_r // 3 + dot_size * 2],
    fill=WHITE,
)

img.save(OUT)
print(f"Icon saved → {OUT}")

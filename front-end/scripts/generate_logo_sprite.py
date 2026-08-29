"""Generate a smooth IIITDMJ 'Orbital Flow' loader sprite.

Design
------
The mark's feather has a green satellite. We remove the static disc and let that
dot travel a calm elliptical orbit inside the green frame — a soft flow trail
follows it. No squash, no spin pops, no white plates. Frames sit on site paper
(#F1F4EC) so the splash never flashes white.

48 frames @ 24fps = 2000ms seamless loop (closed sin / full orbit).
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "public" / "brand"
MARK = BRAND / "iiitdmj-mark-clear.png"
OUT_PNG = BRAND / "iiitdmj-logo-sprite.png"
OUT_JSON = BRAND / "iiitdmj-logo-sprite.json"

PAPER = (241, 244, 236, 255)
FRAMES = 48
SIZE = 200
FPS = 24
DURATION_MS = int(1000 * FRAMES / FPS)

GREEN = (11, 122, 59)
GREEN_BRIGHT = (18, 163, 74)
BLUE = (47, 155, 232)


def smoothstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def make_frame(mark: Image.Image, i: int) -> Image.Image:
    t = i / FRAMES
    # Closed loop — C1-ish via sin/cos only
    canvas = Image.new("RGBA", (SIZE, SIZE), PAPER)
    cx = cy = SIZE / 2

    # Ambient breath — tiny, not poppy (max ~1.5%)
    breath = 1.0 + 0.015 * math.sin(2 * math.pi * t)

    # Soft under-glow (green → blue shift along orbit)
    glow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gr = int(58 + 6 * math.sin(2 * math.pi * t))
    ga = int(22 + 10 * (0.5 + 0.5 * math.sin(2 * math.pi * t)))
    gd.ellipse((cx - gr, cy - gr + 4, cx + gr, cy + gr + 4), fill=(*GREEN, ga))
    glow = glow.filter(ImageFilter.GaussianBlur(18))
    canvas = Image.alpha_composite(canvas, glow)

    # Mark — almost still; micro float only
    float_y = 1.6 * math.sin(2 * math.pi * t)
    mw = int(mark.width * (SIZE * 0.62 / max(mark.width, mark.height)) * breath)
    mh = int(mark.height * (SIZE * 0.62 / max(mark.width, mark.height)) * breath)
    m = mark.resize((mw, mh), Image.Resampling.LANCZOS)
    mx = int(cx - mw / 2)
    my = int(cy - mh / 2 + float_y)
    layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    layer.paste(m, (mx, my), m)
    canvas = Image.alpha_composite(canvas, layer)

    # Orbital path — ellipse hugging the frame (starts at feather-satellite home)
    # Original disc sits ~upper-right; angle 0 = east, we start ~ -50°
    rx, ry = 54.0, 50.0
    home = -0.95  # radians ~ feather tip quadrant
    ang = home + 2 * math.pi * t

    # Flow trail (previous positions)
    trail = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    td = ImageDraw.Draw(trail)
    trail_n = 14
    for k in range(trail_n, 0, -1):
        u = t - k / FRAMES
        a = home + 2 * math.pi * u
        px = cx + rx * math.cos(a)
        py = cy + ry * math.sin(a)
        fade = 1 - k / (trail_n + 1)
        fade = smoothstep(fade)
        rad = 2.2 + 2.8 * fade
        alpha = int(18 + 110 * fade * fade)
        # Blend green → blue along trail
        mix = 0.35 * (1 - fade)
        col = (
            int(GREEN_BRIGHT[0] * (1 - mix) + BLUE[0] * mix),
            int(GREEN_BRIGHT[1] * (1 - mix) + BLUE[1] * mix),
            int(GREEN_BRIGHT[2] * (1 - mix) + BLUE[2] * mix),
            alpha,
        )
        td.ellipse((px - rad, py - rad, px + rad, py + rad), fill=col)
    trail = trail.filter(ImageFilter.GaussianBlur(0.8))
    canvas = Image.alpha_composite(canvas, trail)

    # Faint flow ribbon (arc segment ahead of the dot)
    ribbon = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ribbon)
    for s in range(0, 40):
        a0 = ang + s * 0.012
        a1 = ang + (s + 1) * 0.012
        x0 = cx + rx * math.cos(a0)
        y0 = cy + ry * math.sin(a0)
        x1 = cx + rx * math.cos(a1)
        y1 = cy + ry * math.sin(a1)
        alpha = int(50 * (1 - s / 40) ** 1.6)
        rd.line((x0, y0, x1, y1), fill=(*GREEN, alpha), width=2)
    ribbon = ribbon.filter(ImageFilter.GaussianBlur(0.6))
    canvas = Image.alpha_composite(canvas, ribbon)

    # The satellite itself — soft disc + specular
    dx = cx + rx * math.cos(ang)
    dy = cy + ry * math.sin(ang)
    sat = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sat)
    # Outer bloom
    sd.ellipse((dx - 11, dy - 11, dx + 11, dy + 11), fill=(*GREEN, 40))
    sat = sat.filter(ImageFilter.GaussianBlur(3.5))
    canvas = Image.alpha_composite(canvas, sat)
    # Core
    core = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    cd = ImageDraw.Draw(core)
    r = 5.4
    cd.ellipse((dx - r, dy - r, dx + r, dy + r), fill=(*GREEN_BRIGHT, 245))
    # Specular highlight
    cd.ellipse(
        (dx - r * 0.45, dy - r * 0.65, dx + r * 0.1, dy - r * 0.1),
        fill=(220, 245, 230, 160),
    )
    canvas = Image.alpha_composite(canvas, core)

    return canvas


def main() -> None:
    if not MARK.exists():
        raise SystemExit(f"Run prepare_brand_assets.py first — missing {MARK}")

    mark = Image.open(MARK).convert("RGBA")
    bbox = mark.getbbox()
    if bbox:
        mark = mark.crop(bbox)

    frames = [make_frame(mark, i) for i in range(FRAMES)]
    sheet = Image.new("RGBA", (SIZE * FRAMES, SIZE), PAPER)
    for i, fr in enumerate(frames):
        sheet.paste(fr, (i * SIZE, 0))

    sheet.save(OUT_PNG, optimize=True)
    meta = {
        "name": "iiitdmj-orbital-flow",
        "src": "/brand/iiitdmj-logo-sprite.png",
        "frames": FRAMES,
        "frameWidth": SIZE,
        "frameHeight": SIZE,
        "fps": FPS,
        "durationMs": DURATION_MS,
        "layout": "horizontal",
        "loop": True,
        "paper": "#F1F4EC",
        "motion": ["orbital-satellite", "flow-trail", "soft-glow", "micro-float"],
    }
    OUT_JSON.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"wrote {OUT_PNG} ({sheet.size[0]}x{sheet.size[1]})")
    print(f"{FRAMES} frames @ {FPS}fps = {DURATION_MS}ms")


if __name__ == "__main__":
    main()

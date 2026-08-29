"""Clean IIITDMJ brand assets: corner-flood white plates; lift feather satellite into interior white."""

from __future__ import annotations

from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
BRAND = PUBLIC / "brand"
PAPER = (241, 244, 236, 255)


def flood_knock_background(im: Image.Image) -> Image.Image:
    """Make only the exterior white plate transparent (corner flood). Keeps interior white."""
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()

    def is_plate(x: int, y: int) -> bool:
        r, g, b, a = px[x, y]
        if a < 10:
            return True
        return r > 248 and g > 248 and b > 248

    seen = [[False] * w for _ in range(h)]
    q: deque[tuple[int, int]] = deque()
    for seed in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        if is_plate(*seed):
            q.append(seed)
            seen[seed[1]][seed[0]] = True

    while q:
        x, y = q.popleft()
        px[x, y] = (0, 0, 0, 0)
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx] and is_plate(nx, ny):
                seen[ny][nx] = True
                q.append((nx, ny))

    # Soft fringe on remaining near-white exterior crumbs (alpha already 0 skipped)
    return im


def lift_satellite_to_interior(im: Image.Image) -> Image.Image:
    """Paint out the green disc with the logo's interior white — do NOT punch a hole."""
    w, h = im.size
    # Known layout: disc sits upper-right inside the frame, beside the feather tip
    cx, cy = w * 0.705, h * 0.265
    rad = min(w, h) * 0.072

    # Soft mask
    mask = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(max(1.0, rad * 0.12)))

    out = im.copy()
    px = out.load()
    mpx = mask.load()
    for y in range(h):
        for x in range(w):
            m = mpx[x, y]
            if m < 8:
                continue
            r, g, b, a = px[x, y]
            if a < 20:
                continue
            # Only replace green disc pixels (never the blue feather, never dark navy bar)
            greenish = g > r + 18 and g > b + 12 and g > 90
            if not greenish:
                continue
            # Skip very dark green frame strokes (low luminance)
            if (r + g + b) / 3 < 70:
                continue
            t = m / 255.0
            # Blend toward interior white of the badge
            nr = int(r * (1 - t) + 255 * t)
            ng = int(g * (1 - t) + 255 * t)
            nb = int(b * (1 - t) + 255 * t)
            px[x, y] = (nr, ng, nb, 255)

    print(f"satellite painted out @ ({cx:.1f},{cy:.1f}) r={rad:.1f}")
    return out


def on_paper(im: Image.Image) -> Image.Image:
    bg = Image.new("RGBA", im.size, PAPER)
    return Image.alpha_composite(bg, im.convert("RGBA"))


def process_mark(src: Path, clear: Path, paper: Path, also: Path | None = None) -> None:
    im = flood_knock_background(Image.open(src))
    im = lift_satellite_to_interior(im)
    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)
    im.save(clear)
    on_paper(im).save(paper)
    if also:
        im.save(also)


def process_header(src: Path) -> None:
    im = flood_knock_background(Image.open(src))
    # Satellite only in left mark
    w, h = im.size
    left = im.crop((0, 0, int(w * 0.42), h))
    left = lift_satellite_to_interior(left)
    im.paste(left, (0, 0))
    # re-apply left alpha: paste without mask may lose transparency on plate —
    # rebuild: paste using left as both
    base = flood_knock_background(Image.open(src))
    base.paste(left, (0, 0), left)
    base.save(BRAND / "iiitdmj-org-header-clear.png")
    on_paper(base).save(BRAND / "iiitdmj-org-header-paper.png")
    base.save(src)


def main() -> None:
    import shutil

    BRAND.mkdir(parents=True, exist_ok=True)
    # Prefer pristine sources so re-runs don't compound edits
    src_logo = BRAND / "_source-logo.png"
    src_header = BRAND / "_source-org-header.png"
    if src_logo.exists():
        shutil.copy2(src_logo, PUBLIC / "iiitdmj-logo.png")
    if src_header.exists():
        shutil.copy2(src_header, BRAND / "iiitdmj-org-header.png")

    process_mark(
        PUBLIC / "iiitdmj-logo.png",
        BRAND / "iiitdmj-mark-clear.png",
        BRAND / "iiitdmj-mark-paper.png",
        also=PUBLIC / "iiitdmj-logo.png",
    )
    process_header(BRAND / "iiitdmj-org-header.png")
    print("brand assets ready")


if __name__ == "__main__":
    main()

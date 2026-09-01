"""
INFINI image optimizer — shared by every upload endpoint.

Problem this fixes: phone camera photos are routinely 8-15MB, straight off
the camera at full resolution. Every upload was being stored and served at
that full size, which is why uploads felt slow (client -> server transfer)
and pages felt slow (server -> browser transfer, on every visitor, every
time). Nothing in the pipeline ever resized or re-compressed anything.

What this does for an incoming image:
  1. Auto-rotates using EXIF orientation (phones store "portrait" photos
     rotated + a flag; without this fix images can display sideways once
     the EXIF tag itself is stripped by re-saving).
  2. Downscales so the longest side is at most MAX_DIMENSION px — plenty
     for any phone/web display, since no UI element in this app renders
     an image anywhere near 4000px wide.
  3. Re-encodes as JPEG (or WEBP for images that need alpha transparency)
     at a quality level that's visually near-lossless but a fraction of
     the file size.
  4. Returns BOTH the optimized bytes (what gets served normally) and the
     original untouched bytes (kept alongside so users can still download
     the true original later if they want full quality/EXIF/etc).

Non-image files (video, etc.) pass through untouched — this module only
ever touches image bytes.
"""

from __future__ import annotations

import io
from typing import Optional

MAX_DIMENSION = 1920      # longest side, in pixels — generous for any on-screen use
JPEG_QUALITY = 85         # visually near-lossless for photos at this resolution
WEBP_QUALITY = 85

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".heic", ".heif"}


def is_optimizable_image(filename: str) -> bool:
    from pathlib import Path
    return Path(filename).suffix.lower() in IMAGE_EXTENSIONS


def optimize_image_bytes(raw: bytes, filename: str) -> tuple[bytes, str, bool]:
    """
    Try to optimize `raw` image bytes.

    Returns (optimized_bytes, optimized_ext, changed):
      - optimized_bytes: smaller/re-encoded bytes, or the original bytes
        unchanged if optimization wasn't possible/beneficial.
      - optimized_ext: file extension to use for the optimized copy
        (".jpg" or ".webp" — whichever it was actually encoded as).
      - changed: False if optimization failed or wasn't applicable (e.g.
        animated GIF, or Pillow unavailable) — caller should treat the
        original bytes/extension as-is in that case.
    """
    from pathlib import Path

    ext = Path(filename).suffix.lower()
    if ext not in IMAGE_EXTENSIONS:
        return raw, ext or ".bin", False

    try:
        from PIL import Image, ImageOps
    except Exception:
        return raw, ext, False

    try:
        im = Image.open(io.BytesIO(raw))

        # Animated images (GIF/WEBP) — don't touch, we'd only keep frame 1.
        if getattr(im, "is_animated", False):
            return raw, ext, False

        im = ImageOps.exif_transpose(im)  # bake in correct rotation

        has_alpha = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)

        w, h = im.size
        if max(w, h) > MAX_DIMENSION:
            scale = MAX_DIMENSION / float(max(w, h))
            im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)

        out = io.BytesIO()
        if has_alpha:
            im = im.convert("RGBA")
            im.save(out, format="WEBP", quality=WEBP_QUALITY, method=4)
            new_ext = ".webp"
        else:
            im = im.convert("RGB")
            im.save(out, format="JPEG", quality=JPEG_QUALITY, optimize=True)
            new_ext = ".jpg"

        optimized = out.getvalue()

        # Only "win" if we actually made it smaller — otherwise keep original
        # (protects small/simple images, like tiny icons, from getting worse).
        if len(optimized) < len(raw):
            return optimized, new_ext, True
        return raw, ext, False

    except Exception:
        # Any decode/encode failure: never block the upload over this,
        # just fall back to storing the original bytes untouched.
        return raw, ext, False

"""
generate_thumbnail_canva_cloudinary.py
Replaces generate_thumbnail.py

HOW IT WORKS:
  1. You design ONE thumbnail template per channel in Canva (free)
  2. Export it as PNG, upload to Cloudinary
  3. This script uses Cloudinary's FREE transformation API to overlay
     the title text automatically -- no Canva API needed, no Enterprise plan

The Cloudinary text overlay is completely free and unlimited.
The final thumbnail looks exactly like your Canva design with auto-filled text.

SETUP (one-time per channel, ~5 minutes):
  1. Open Canva → create a 1280x720 design
  2. Design your thumbnail template (background, shapes, branding)
  3. Leave a DARK area for the text to sit on
  4. Download as PNG
  5. Upload to Cloudinary: dopamine-studios/CH1/thumbnail-template
  6. Done -- this script handles everything else automatically
"""

import json
import os
import sys
import tempfile
import base64
from datetime import datetime, timezone

import cloudinary
import cloudinary.uploader
import cloudinary.api
import cloudinary.utils
import requests

cloudinary.config(
    cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
    api_key=os.environ["CLOUDINARY_API_KEY"],
    api_secret=os.environ["CLOUDINARY_API_SECRET"],
    secure=True,
)

CHANNEL_ID = os.environ.get("CHANNEL_ID", "CH1")
DATE_STR   = datetime.now(timezone.utc).strftime("%Y-%m-%d")

# Per-channel typography config
CHANNEL_FONTS = {
    "CH1": {"font": "Anton", "color": "e8ff47", "size": 90, "gravity": "west", "x": 60},
    "CH2": {"font": "Anton", "color": "ffffff", "size": 85, "gravity": "west", "x": 60},
    "CH3": {"font": "Anton", "color": "ff3333", "size": 85, "gravity": "west", "x": 60},
    "CH4": {"font": "Anton", "color": "ffffff", "size": 85, "gravity": "center", "x": 0},
    "CH5": {"font": "Anton", "color": "c8a24b", "size": 80, "gravity": "west", "x": 60},
}


def log(msg: str):
    print(f"[{CHANNEL_ID}][Thumbnail] {msg}", flush=True)


def fetch_manifest() -> dict | None:
    public_id = f"dopamine-studios/{CHANNEL_ID}/manifests/{DATE_STR}"
    try:
        result = cloudinary.api.resource(public_id, resource_type="raw")
        resp = requests.get(result["secure_url"], timeout=10)
        return resp.json()
    except Exception as e:
        log(f"[ERROR] No manifest: {e}")
        return None


def template_exists() -> bool:
    """Check if the Canva template has been uploaded to Cloudinary."""
    try:
        cloudinary.api.resource(
            f"dopamine-studios/{CHANNEL_ID}/thumbnail-template",
            resource_type="image"
        )
        return True
    except Exception:
        return False


def generate_with_cloudinary_overlay(title: str, font_config: dict) -> str | None:
    """
    Use Cloudinary's free transformation API to overlay text on the Canva template.
    Returns the URL of the generated thumbnail.
    """
    template_id = f"dopamine-studios/{CHANNEL_ID}/thumbnail-template"

    # Clean title for Cloudinary text overlay
    # Max 4 words, uppercase, remove special chars
    words = title.upper().split()[:4]
    clean_title = " ".join(words)
    # Cloudinary requires encoding special chars
    clean_title = clean_title.replace(",", "").replace(".", "").replace("!", "").replace("?", "")

    font  = font_config["font"]
    color = font_config["color"]
    size  = font_config["size"]
    grav  = font_config["gravity"]
    x_off = font_config["x"]

    # Build Cloudinary transformation URL with text overlay
    transformation = [
        {"width": 1280, "height": 720, "crop": "fill"},
        {
            "overlay": {
                "font_family": font,
                "font_size": size,
                "font_weight": "bold",
                "text": clean_title,
                "text_align": "left",
                "letter_spacing": -2,
            },
            "color": f"#{color}",
            "gravity": grav,
            "x": x_off,
            "y": 0,
        },
    ]

    url, _ = cloudinary.utils.cloudinary_url(
        template_id,
        transformation=transformation,
        format="jpg",
        secure=True,
    )

    log(f"Cloudinary overlay URL generated.")
    return url


def generate_fallback_thumbnail(title: str, font_config: dict) -> str | None:
    """
    Fallback when no Canva template exists yet.
    Creates a clean programmatic thumbnail using Cloudinary's text API
    (no template image needed -- pure Cloudinary).
    """
    from PIL import Image, ImageDraw

    # Channel background colors
    BG_COLORS = {
        "CH1": "#0a0a0a", "CH2": "#0d1117",
        "CH3": "#0d0d0d", "CH4": "#0a0a1a", "CH5": "#1a1008",
    }
    ACCENT_COLORS = {
        "CH1": "#e8ff47", "CH2": "#00d4aa",
        "CH3": "#ff3333", "CH4": "#7b61ff", "CH5": "#c8a24b",
    }

    bg_color     = BG_COLORS.get(CHANNEL_ID, "#0a0a0a")
    accent_color = ACCENT_COLORS.get(CHANNEL_ID, "#ffffff")

    img  = Image.new("RGB", (1280, 720), bg_color)
    draw = ImageDraw.Draw(img)

    # Accent bar left edge
    draw.rectangle([0, 0, 14, 720], fill=accent_color)

    # Channel label top right
    try:
        from PIL import ImageFont
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_config["size"])
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
    except Exception:
        font_large = ImageFont.load_default()
        font_small = font_large

    channel_names = {
        "CH1": "DOPAMINE LOOP", "CH2": "FINANCE",
        "CH3": "CONSPIRACY", "CH4": "PSYCHOLOGY", "CH5": "HISTORY",
    }
    draw.text((40, 30), channel_names.get(CHANNEL_ID, CHANNEL_ID),
              font=font_small, fill=accent_color)

    # Main title -- wrap to 3 lines max
    words = title.upper().split()
    lines, line = [], []
    for word in words:
        test = " ".join(line + [word])
        bbox = draw.textbbox((0, 0), test, font=font_large)
        if bbox[2] > 1180:
            if line: lines.append(" ".join(line))
            line = [word]
        else:
            line.append(word)
    if line: lines.append(" ".join(line))
    lines = lines[:3]

    total_h = len(lines) * (font_config["size"] + 10)
    y_start = (720 - total_h) // 2

    for idx, ln in enumerate(lines):
        y = y_start + idx * (font_config["size"] + 10)
        # Shadow
        draw.text((42, y + 2), ln, font=font_large, fill="#000000")
        # Text
        draw.text((40, y), ln, font=font_large, fill="#ffffff")
        # Last word in accent color
        if idx == len(lines) - 1:
            parts = ln.rsplit(" ", 1)
            if len(parts) == 2:
                prefix_w = draw.textbbox((0, 0), parts[0] + " ", font=font_large)[2]
                draw.text((40 + prefix_w, y), parts[1], font=font_large, fill=accent_color)

    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    img.save(tmp.name, "JPEG", quality=95)
    tmp.close()
    return tmp.name


def main():
    log(f"Thumbnail generation started -- {DATE_STR}")

    manifest = fetch_manifest()
    if not manifest:
        sys.exit(0)

    seo   = manifest.get("seo", {})
    title = seo.get("title", manifest.get("topic", "Video"))
    log(f"Title: {title}")

    font_config = CHANNEL_FONTS.get(CHANNEL_ID, CHANNEL_FONTS["CH1"])

    thumb_url  = None
    local_path = None

    if template_exists():
        # Use Canva template + Cloudinary overlay
        log("Canva template found -- using Cloudinary overlay.")
        thumb_url = generate_with_cloudinary_overlay(title, font_config)
    else:
        # Fallback -- programmatic thumbnail
        log("No Canva template yet -- using programmatic fallback.")
        log("  → To use your Canva design: upload PNG to Cloudinary:")
        log(f"     dopamine-studios/{CHANNEL_ID}/thumbnail-template")
        local_path = generate_fallback_thumbnail(title, font_config)

    # Upload to Cloudinary for pipeline use
    public_id = f"dopamine-studios/{CHANNEL_ID}/thumbnails/{DATE_STR}"

    if local_path:
        result = cloudinary.uploader.upload(
            local_path, public_id=public_id,
            resource_type="image", overwrite=True,
        )
        os.remove(local_path)
        log(f"Thumbnail uploaded: {result['secure_url']}")
    elif thumb_url:
        # Download the Cloudinary-generated URL and re-upload with correct public_id
        resp = requests.get(thumb_url, timeout=30)
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        tmp.write(resp.content)
        tmp.close()
        result = cloudinary.uploader.upload(
            tmp.name, public_id=public_id,
            resource_type="image", overwrite=True,
        )
        os.remove(tmp.name)
        log(f"Canva overlay thumbnail uploaded: {result['secure_url']}")

    log("[DONE] Thumbnail ready.")


if __name__ == "__main__":
    main()

"""
generate_thumbnail.py
Generates a YouTube thumbnail for today's video.
Uses Cloudinary's transformation API to overlay text on a template image.
Falls back to Pillow-generated thumbnail if no template exists.
"""

import base64
import json
import os
import sys
import tempfile
from datetime import datetime, timezone

import cloudinary
import cloudinary.uploader
import cloudinary.api
import requests
from PIL import Image, ImageDraw, ImageFont

cloudinary.config(
    cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
    api_key=os.environ["CLOUDINARY_API_KEY"],
    api_secret=os.environ["CLOUDINARY_API_SECRET"],
    secure=True,
)

CHANNEL_ID = os.environ.get("CHANNEL_ID", "CH1")
DATE_STR   = datetime.now(timezone.utc).strftime("%Y-%m-%d")

THUMBNAIL_W = 1280
THUMBNAIL_H = 720


def log(msg: str):
    print(f"[{CHANNEL_ID}] {msg}", flush=True)


def fetch_manifest() -> dict | None:
    public_id = f"dopamine-studios/{CHANNEL_ID}/manifests/{DATE_STR}"
    try:
        result = cloudinary.api.resource(public_id, resource_type="raw")
        resp   = requests.get(result["secure_url"], timeout=10)
        return resp.json()
    except Exception as e:
        log(f"[ERROR] No manifest: {e}")
        return None


def load_config() -> dict:
    path = f"configs/channel-config-{CHANNEL_ID.lower()}.json"
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def hex_to_rgb(hex_color: str) -> tuple:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def generate_pillow_thumbnail(title: str, config: dict, output_path: str):
    """
    Fallback: generate a clean thumbnail using Pillow.
    Bold title text on channel-colored background.
    """
    palette      = config.get("visual", {}).get("palette", {})
    bg_color     = hex_to_rgb(palette.get("primary", "#0a0a0a"))
    accent_color = hex_to_rgb(palette.get("accent", "#e8ff47"))
    text_color   = hex_to_rgb(palette.get("text", "#ffffff"))

    img  = Image.new("RGB", (THUMBNAIL_W, THUMBNAIL_H), bg_color)
    draw = ImageDraw.Draw(img)

    # Accent bar on left edge
    draw.rectangle([0, 0, 12, THUMBNAIL_H], fill=accent_color)

    # Channel name top right
    channel_name = config.get("channel_name", CHANNEL_ID)
    try:
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
    except Exception:
        font_small = ImageFont.load_default()
        font_large = ImageFont.load_default()

    draw.text((40, 40), channel_name.upper(), font=font_small, fill=accent_color)

    # Wrap title text
    words = title.split()
    lines, line = [], []
    for word in words:
        test = " ".join(line + [word])
        bbox = draw.textbbox((0, 0), test, font=font_large)
        if bbox[2] > THUMBNAIL_W - 80:
            if line:
                lines.append(" ".join(line))
            line = [word]
        else:
            line.append(word)
    if line:
        lines.append(" ".join(line))
    lines = lines[:3]  # Max 3 lines

    total_h = len(lines) * 90
    y_start = (THUMBNAIL_H - total_h) // 2

    for i, ln in enumerate(lines):
        # Shadow
        draw.text((42, y_start + i * 90 + 2), ln, font=font_large, fill=(0, 0, 0))
        # Text
        draw.text((40, y_start + i * 90), ln, font=font_large, fill=text_color)

    img.save(output_path, "JPEG", quality=95)
    log(f"Pillow thumbnail generated: {output_path}")


def try_cloudinary_template_thumbnail(title: str, config: dict, output_path: str) -> bool:
    """
    Try to use a Cloudinary image transformation overlay on a template.
    Returns True if successful.
    """
    template_id = f"dopamine-studios/{CHANNEL_ID}/assets/thumbnail-template"
    try:
        # Check template exists
        cloudinary.api.resource(template_id, resource_type="image")
    except Exception:
        log("  No Cloudinary thumbnail template found — using Pillow fallback.")
        return False

    try:
        palette  = config.get("visual", {}).get("palette", {})
        text_color = palette.get("text", "white").lstrip("#")
        safe_title = title[:80].replace("/", " ").replace(",", " ")

        # Generate URL with text overlay
        url = cloudinary.utils.cloudinary_url(
            template_id,
            width=THUMBNAIL_W,
            height=THUMBNAIL_H,
            crop="fill",
            overlay={
                "font_family": "Arial",
                "font_size": 70,
                "font_weight": "bold",
                "text": safe_title,
                "color": text_color,
            },
            gravity="west",
            x=60,
            y=0,
        )[0]

        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(resp.content)
            log(f"  Cloudinary template thumbnail generated.")
            return True
    except Exception as e:
        log(f"  Cloudinary thumbnail failed: {e}")

    return False


def main():
    log(f"Thumbnail generation started — {DATE_STR}")

    manifest = fetch_manifest()
    if not manifest:
        sys.exit(1)

    config = load_config()
    seo    = manifest.get("seo", {})
    title  = seo.get("title", manifest.get("topic", "Video"))

    log(f"Title: {title}")

    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    tmp.close()
    output_path = tmp.name

    # Try Cloudinary template first, fall back to Pillow
    if not try_cloudinary_template_thumbnail(title, config, output_path):
        generate_pillow_thumbnail(title, config, output_path)

    # Upload to Cloudinary
    public_id = f"dopamine-studios/{CHANNEL_ID}/thumbnails/{DATE_STR}"
    result = cloudinary.uploader.upload(
        output_path,
        public_id=public_id,
        resource_type="image",
        overwrite=True,
    )
    log(f"Thumbnail uploaded: {result['secure_url']}")

    try:
        os.remove(output_path)
    except Exception:
        pass

    log("[DONE] Thumbnail ready.")


if __name__ == "__main__":
    main()

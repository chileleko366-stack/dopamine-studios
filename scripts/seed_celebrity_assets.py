"""
seed_celebrity_assets.py

One-time (or occasional) helper to populate cutout PNGs for celebrities that
have public-domain or Creative Commons photos available via Wikipedia /
Wikimedia Commons.

Strategy:
  1. Reads configs/celebrity-assets.json
  2. For every celebrity with cutout_url=null and source_type='none':
     a. Queries Wikimedia Commons for portraits matching the name
     b. Picks the best candidate (largest, properly licensed)
     c. Downloads it
     d. Uploads to Cloudinary with auto-background-removal transformation
     e. Updates the manifest in-place with the new URL
  3. Reports what it found, what it skipped, what failed

Usage:
    python scripts/seed_celebrity_assets.py
    python scripts/seed_celebrity_assets.py --celebrity steve_jobs
    python scripts/seed_celebrity_assets.py --dry-run

Requires Cloudinary's background removal add-on (free tier: 50/month). If
not enabled, the script uploads the source photo as-is and notes it needs
manual cutout.
"""

import argparse
import json
import os
import sys
import time
import urllib.parse
from typing import Optional

import requests
import cloudinary
import cloudinary.uploader

CONFIG_PATH = "configs/celebrity-assets.json"

cloudinary.config(
    cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
    api_key=os.environ["CLOUDINARY_API_KEY"],
    api_secret=os.environ["CLOUDINARY_API_SECRET"],
    secure=True,
)

# Wikimedia Commons API
WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"

USER_AGENT = "DopamineStudiosBot/1.0 (https://github.com/chileleko366-stack/dopamine-studios; contact: chileleko366@gmail.com)"

# Licenses we accept as public-domain or compatible
ACCEPTABLE_LICENSES = {
    "pd",
    "publicdomain",
    "cc0",
    "cc-by",
    "cc-by-sa",
    "cc-by-sa-2.0",
    "cc-by-sa-3.0",
    "cc-by-sa-4.0",
    "cc-by-2.0",
    "cc-by-3.0",
    "cc-by-4.0",
}


def log(msg: str):
    print(f"[seed] {msg}", flush=True)


def search_wikipedia_for_main_image(display_name: str) -> Optional[dict]:
    """
    Use the Wikipedia API to find the page for a celebrity, then get the
    primary image (page_image) used in their infobox. Returns dict with
    url + license info, or None.
    """
    headers = {"User-Agent": USER_AGENT}
    # 1. Find the Wikipedia page
    params = {
        "action": "query",
        "format": "json",
        "titles": display_name,
        "prop": "pageimages|pageprops",
        "pithumbsize": 2000,
    }
    try:
        r = requests.get(WIKIPEDIA_API, params=params, headers=headers, timeout=15)
        r.raise_for_status()
        pages = r.json().get("query", {}).get("pages", {})
        for page_id, page in pages.items():
            if "thumbnail" in page:
                return {
                    "url": page["thumbnail"]["source"],
                    "filename": page.get("pageimage"),
                    "page_title": page.get("title"),
                }
    except Exception as e:
        log(f"  Wikipedia search failed for {display_name}: {e}")
    return None


def get_license_for_file(filename: str) -> Optional[str]:
    """Given a Wikimedia Commons filename, fetch its license metadata."""
    headers = {"User-Agent": USER_AGENT}
    params = {
        "action": "query",
        "format": "json",
        "titles": f"File:{filename}",
        "prop": "imageinfo",
        "iiprop": "extmetadata",
    }
    try:
        r = requests.get(WIKIMEDIA_API, params=params, headers=headers, timeout=15)
        r.raise_for_status()
        pages = r.json().get("query", {}).get("pages", {})
        for _, page in pages.items():
            info = page.get("imageinfo", [{}])[0]
            ext = info.get("extmetadata", {})
            short_name = ext.get("LicenseShortName", {}).get("value", "").lower().replace(" ", "-")
            return short_name
    except Exception as e:
        log(f"  License lookup failed for {filename}: {e}")
    return None


def is_acceptable_license(license_str: Optional[str]) -> bool:
    if not license_str:
        return False
    license_str = license_str.lower()
    for acceptable in ACCEPTABLE_LICENSES:
        if acceptable in license_str:
            return True
    return False


def upload_to_cloudinary(image_url: str, slug: str, attempt_bg_removal: bool = True) -> Optional[str]:
    """Upload the photo to Cloudinary. Try background removal; fall back to raw upload."""
    public_id = f"dopamine-studios/celebrities/{slug}"
    try:
        upload_args = {
            "public_id": public_id,
            "overwrite": True,
            "format": "png",
        }
        if attempt_bg_removal:
            upload_args["background_removal"] = "cloudinary_ai"
        result = cloudinary.uploader.upload(image_url, **upload_args)
        return result.get("secure_url")
    except cloudinary.exceptions.Error as e:
        msg = str(e)
        if attempt_bg_removal and ("background_removal" in msg or "addon" in msg.lower()):
            log(f"  Cloudinary BG removal addon not enabled; uploading without cutout.")
            return upload_to_cloudinary(image_url, slug, attempt_bg_removal=False)
        log(f"  Upload failed: {e}")
        return None
    except Exception as e:
        log(f"  Upload failed: {e}")
        return None


def seed_one(slug: str, entry: dict, dry_run: bool = False) -> Optional[str]:
    """Seed one celebrity. Returns the new Cloudinary URL or None."""
    display = entry.get("display_name", slug)
    log(f"{slug} ({display})")

    if entry.get("cutout_url"):
        log(f"  Already has cutout_url; skipping.")
        return entry["cutout_url"]

    # 1. Look up on Wikipedia
    candidate = search_wikipedia_for_main_image(display)
    if not candidate:
        log(f"  No Wikipedia article / no image found.")
        return None

    # 2. Verify license
    filename = candidate.get("filename")
    if filename:
        license = get_license_for_file(filename)
        log(f"  Found image. License: {license}")
        if not is_acceptable_license(license):
            log(f"  License not acceptable; skipping (would need licensed/AI alternative).")
            return None
    else:
        log(f"  No filename returned; skipping.")
        return None

    if dry_run:
        log(f"  [DRY-RUN] Would upload: {candidate['url']}")
        return candidate["url"]

    # 3. Upload to Cloudinary with background removal
    cloud_url = upload_to_cloudinary(candidate["url"], slug)
    if cloud_url:
        log(f"  Uploaded: {cloud_url}")
    return cloud_url


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--celebrity", help="Only seed this slug")
    parser.add_argument("--dry-run", action="store_true", help="Look up sources but don't upload")
    args = parser.parse_args()

    with open(CONFIG_PATH) as f:
        manifest = json.load(f)

    celebs = manifest.get("celebrities", {})
    slugs = [args.celebrity] if args.celebrity else list(celebs.keys())

    results = {"seeded": 0, "skipped": 0, "failed": 0}

    for slug in slugs:
        entry = celebs.get(slug)
        if not entry:
            log(f"{slug}: not in manifest, skipping")
            results["skipped"] += 1
            continue

        try:
            new_url = seed_one(slug, entry, dry_run=args.dry_run)
            if new_url and not args.dry_run:
                entry["cutout_url"] = new_url
                entry["source_type"] = "public_domain"
                results["seeded"] += 1
            elif new_url and args.dry_run:
                results["seeded"] += 1
            else:
                results["skipped"] += 1
        except Exception as e:
            log(f"{slug}: ERROR -- {e}")
            results["failed"] += 1

        time.sleep(0.5)  # Be polite to Wikipedia API

    # 4. Save the updated manifest
    if not args.dry_run and results["seeded"] > 0:
        with open(CONFIG_PATH, "w") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        log(f"Manifest updated: {CONFIG_PATH}")

    log(f"\nDone. Seeded: {results['seeded']}, Skipped: {results['skipped']}, Failed: {results['failed']}")

    if results["failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()

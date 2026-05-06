"""
cleanup_cloudinary.py
Deletes all temporary Cloudinary assets after upload confirmation.
Keeps: manifests/published, thumbnails, SEO files.
Deletes: rendered clips, voiceover, final video, render jobs.
"""

import os
import sys
from datetime import datetime, timezone

import cloudinary
import cloudinary.api
import cloudinary.uploader
import requests

cloudinary.config(
    cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
    api_key=os.environ["CLOUDINARY_API_KEY"],
    api_secret=os.environ["CLOUDINARY_API_SECRET"],
    secure=True,
)

CHANNEL_ID = os.environ.get("CHANNEL_ID", "CH1")
DATE_STR   = datetime.now(timezone.utc).strftime("%Y-%m-%d")


def delete_folder_resources(prefix: str, resource_type: str = "video"):
    try:
        result = cloudinary.api.resources(
            type="upload",
            resource_type=resource_type,
            prefix=prefix,
            max_results=100,
        )
        ids = [r["public_id"] for r in result.get("resources", [])]
        if ids:
            cloudinary.api.delete_resources(ids, resource_type=resource_type)
            print(f"  Deleted {len(ids)} {resource_type} files from {prefix}")
    except Exception as e:
        print(f"  [WARN] Cleanup skipped for {prefix}: {e}")


def main():
    print(f"[{CHANNEL_ID}] Cleaning up temp Cloudinary assets for {DATE_STR}...")

    # Verify upload succeeded before deleting
    manifest_id = f"dopamine-studios/{CHANNEL_ID}/manifests/{DATE_STR}"
    try:
        result  = cloudinary.api.resource(manifest_id, resource_type="raw")
        resp    = requests.get(result["secure_url"], timeout=10)
        manifest = resp.json()
        if manifest.get("status") != "uploaded":
            print(f"[{CHANNEL_ID}] Upload not confirmed -- skipping cleanup for safety.")
            sys.exit(0)
    except Exception as e:
        print(f"[{CHANNEL_ID}] Could not verify upload: {e} -- skipping cleanup.")
        sys.exit(0)

    # Delete rendered mograph clips
    delete_folder_resources(
        f"dopamine-studios/{CHANNEL_ID}/rendered/{DATE_STR}", "video")

    # Delete final assembled video
    delete_folder_resources(
        f"dopamine-studios/{CHANNEL_ID}/final/{DATE_STR}", "video")

    # Delete voiceover audio
    delete_folder_resources(
        f"dopamine-studios/{CHANNEL_ID}/voiceover/{DATE_STR}", "raw")

    # Delete render job from queue
    try:
        cloudinary.uploader.destroy(
            f"dopamine-studios/queue/render-job-{CHANNEL_ID}-{DATE_STR}",
            resource_type="raw")
        print(f"  Deleted render job from queue.")
    except Exception:
        pass

    print(f"[{CHANNEL_ID}] Cleanup complete. Thumbnails + SEO + published records kept.")


if __name__ == "__main__":
    main()

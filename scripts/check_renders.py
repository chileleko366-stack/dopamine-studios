"""
check_renders.py
Checks Cloudinary for today's render manifest.
Sets GitHub Actions output: has_renders=true/false
"""

import json
import os
import sys
from datetime import datetime, timezone

import cloudinary
import cloudinary.api
import requests

cloudinary.config(
    cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
    api_key=os.environ["CLOUDINARY_API_KEY"],
    api_secret=os.environ["CLOUDINARY_API_SECRET"],
    secure=True,
)

CHANNEL_ID = os.environ.get("CHANNEL_ID", "CH1")
DATE_STR   = datetime.now(timezone.utc).strftime("%Y-%m-%d")


def set_output(key: str, value: str):
    with open(os.environ.get("GITHUB_OUTPUT", "/dev/null"), "a") as f:
        f.write(f"{key}={value}\n")


def main():
    public_id = f"dopamine-studios/{CHANNEL_ID}/manifests/{DATE_STR}"
    try:
        result = cloudinary.api.resource(public_id, resource_type="raw")
        resp   = requests.get(result["secure_url"], timeout=10)
        manifest = resp.json()
        status = manifest.get("status", "")

        if status == "rendered":
            print(f"[{CHANNEL_ID}] Renders ready ✓")
            set_output("has_renders", "true")
        else:
            print(f"[{CHANNEL_ID}] Manifest status: {status} -- not ready")
            set_output("has_renders", "false")

    except Exception as e:
        print(f"[{CHANNEL_ID}] No manifest found: {e}")
        set_output("has_renders", "false")


if __name__ == "__main__":
    main()

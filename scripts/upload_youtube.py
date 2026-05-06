"""
upload_youtube.py
Runs inside GitHub Actions at 6AM after assembly.
Downloads the final video from Cloudinary, uploads to YouTube
with full metadata from the SEO package in the manifest.

YOUTUBE AUTH SETUP (one-time):
  1. Go to Google Cloud Console → dopamine-loop project
  2. APIs & Services → Credentials → OAuth 2.0 Client IDs
  3. Create Desktop App credentials → download client_secret.json
  4. Run locally once: python get_youtube_token.py
  5. Copy the refresh token to GitHub Actions secret: YOUTUBE_REFRESH_TOKEN
  6. Each channel has its own refresh token for its own YouTube account
"""

import json
import os
import sys
import tempfile
from datetime import datetime, timezone

import cloudinary
import cloudinary.api
import requests

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

cloudinary.config(
    cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
    api_key=os.environ["CLOUDINARY_API_KEY"],
    api_secret=os.environ["CLOUDINARY_API_SECRET"],
    secure=True,
)

CHANNEL_ID = os.environ.get("CHANNEL_ID", "CH1")
DATE_STR   = datetime.now(timezone.utc).strftime("%Y-%m-%d")

# Per-channel YouTube refresh tokens
# GitHub secret names: YOUTUBE_REFRESH_TOKEN_CH1, YOUTUBE_REFRESH_TOKEN_CH2, etc.
# Client ID and Secret are shared across all channels (same Google Cloud project)
CLIENT_ID     = os.environ.get("YOUTUBE_CLIENT_ID")
CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET")
REFRESH_TOKEN = os.environ.get(f"YOUTUBE_REFRESH_TOKEN_{CHANNEL_ID}")

YOUTUBE_CATEGORY_IDS = {
    "motivation":    "26",   # Howto & Style
    "finance":       "25",   # News & Politics
    "conspiracy":    "25",
    "psychology":    "27",   # Education
    "history":       "27",
}


def log(msg: str):
    print(f"[{CHANNEL_ID}] {msg}", flush=True)


def get_youtube_service():
    """Build authenticated YouTube service using stored refresh token."""
    creds = Credentials(
        token=None,
        refresh_token=REFRESH_TOKEN,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
    )
    creds.refresh(Request())
    return build("youtube", "v3", credentials=creds)


def fetch_manifest() -> dict | None:
    public_id = f"dopamine-studios/{CHANNEL_ID}/manifests/{DATE_STR}"
    try:
        result = cloudinary.api.resource(public_id, resource_type="raw")
        resp = requests.get(result["secure_url"], timeout=15)
        return resp.json()
    except Exception as e:
        log(f"[ERROR] Could not fetch manifest: {e}")
        return None


def load_config() -> dict:
    path = f"configs/channel-config-{CHANNEL_ID.lower()}.json"
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def download_video(url: str) -> str:
    """Download final video from Cloudinary to a temp file."""
    tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    log(f"Downloading final video...")
    resp = requests.get(url, stream=True, timeout=300)
    resp.raise_for_status()
    for chunk in resp.iter_content(chunk_size=8192):
        tmp.write(chunk)
    tmp.close()
    log(f"Downloaded to: {tmp.name}")
    return tmp.name


def fetch_thumbnail(manifest: dict) -> str | None:
    """Download thumbnail from Cloudinary if it exists."""
    public_id = f"dopamine-studios/{CHANNEL_ID}/thumbnails/{DATE_STR}"
    try:
        result = cloudinary.api.resource(public_id, resource_type="image")
        url = result["secure_url"]
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        resp = requests.get(url, timeout=30)
        tmp.write(resp.content)
        tmp.close()
        return tmp.name
    except Exception:
        log("[WARN] No thumbnail found -- YouTube will auto-generate.")
        return None


def build_scheduled_datetime(config: dict) -> str:
    """
    Build ISO 8601 publish time from config upload_time.
    Always schedules for today at the configured time.
    """
    upload_time = config.get("schedule", {}).get("upload_time", "08:00")
    hour, minute = map(int, upload_time.split(":"))
    now = datetime.now(timezone.utc)
    scheduled = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    # If that time has already passed today, add 1 day
    if scheduled <= now:
        from datetime import timedelta
        scheduled += timedelta(days=1)
    return scheduled.strftime("%Y-%m-%dT%H:%M:%SZ")


def upload_to_youtube(youtube, video_path: str, seo: dict, config: dict, is_short: bool = False) -> str:
    """Upload video to YouTube and return the video ID."""
    title       = seo.get("title", "Untitled")[:100]
    description = seo.get("description", "")[:5000]
    tags        = seo.get("tags", [])[:500]
    hashtags    = seo.get("hashtags", [])
    category    = seo.get("category_id", "27")
    privacy     = "private"   # Will be published at scheduled time

    # Append hashtags to description
    if hashtags:
        description += "\n\n" + " ".join(hashtags)

    publish_at = build_scheduled_datetime(config)
    log(f"Scheduling publish at: {publish_at}")

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category,
        },
        "status": {
            "privacyStatus": "private",
            "publishAt": publish_at,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=5 * 1024 * 1024,  # 5MB chunks
    )

    log(f"Uploading: {title}")
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            log(f"  Upload progress: {pct}%")

    video_id = response.get("id")
    log(f"Uploaded! Video ID: {video_id}")
    return video_id


def set_thumbnail(youtube, video_id: str, thumbnail_path: str):
    """Set custom thumbnail on uploaded video."""
    try:
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumbnail_path, mimetype="image/jpeg"),
        ).execute()
        log(f"Thumbnail set for video {video_id}")
    except Exception as e:
        log(f"[WARN] Thumbnail upload failed: {e}")


def update_manifest_uploaded(manifest: dict, video_id: str):
    """Mark manifest as uploaded with YouTube video ID."""
    import base64
    manifest["youtube_video_id"] = video_id
    manifest["status"] = "uploaded"
    manifest["uploaded_at"] = datetime.now(timezone.utc).isoformat()
    manifest_str = json.dumps(manifest, indent=2)
    encoded = base64.b64encode(manifest_str.encode()).decode()
    cloudinary.uploader.upload(
        f"data:text/plain;base64,{encoded}",
        public_id=f"dopamine-studios/{CHANNEL_ID}/manifests/{DATE_STR}",
        resource_type="raw",
        overwrite=True,
    )
    # Also save to permanent published record
    cloudinary.uploader.upload(
        f"data:text/plain;base64,{encoded}",
        public_id=f"dopamine-studios/{CHANNEL_ID}/published/{DATE_STR}",
        resource_type="raw",
        overwrite=False,
    )


def main():
    log(f"YouTube upload started -- {DATE_STR}")

    manifest = fetch_manifest()
    if not manifest:
        log("[ERROR] No manifest found. Aborting.")
        sys.exit(0)  # Clean exit -- not a failure

    if manifest.get("status") != "assembled":
        log(f"[ERROR] Manifest status '{manifest.get('status')}' -- not assembled yet.")
        sys.exit(0)  # Clean exit -- not a failure

    final_url = manifest.get("final_video_url")
    if not final_url:
        log("[ERROR] No final_video_url in manifest. Assembly may have failed.")
        sys.exit(0)  # Clean exit -- not a failure

    config = load_config()
    seo    = manifest.get("seo", {})

    if not CLIENT_ID or not REFRESH_TOKEN:
        log("[SKIP] No YouTube token for this channel yet -- video ready in Cloudinary.")
        log(f"  Add YOUTUBE_REFRESH_TOKEN_{CHANNEL_ID} to GitHub secrets to enable auto-upload.")
        log(f"  Final video waiting at: dopamine-studios/{CHANNEL_ID}/final/{DATE_STR}/video")
        sys.exit(0)  # Clean exit -- not a failure

    youtube       = get_youtube_service()
    video_path    = download_video(final_url)
    thumbnail_path = fetch_thumbnail(manifest)

    try:
        video_id = upload_to_youtube(youtube, video_path, seo, config)

        if thumbnail_path:
            set_thumbnail(youtube, video_id, thumbnail_path)

        update_manifest_uploaded(manifest, video_id)
        log(f"\n[DONE] Video live: https://youtu.be/{video_id}")

    finally:
        try:
            os.remove(video_path)
        except Exception:
            pass
        if thumbnail_path:
            try:
                os.remove(thumbnail_path)
            except Exception:
                pass


if __name__ == "__main__":
    main()

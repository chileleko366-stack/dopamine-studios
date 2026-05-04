"""
upload_to_drive.py
Runs inside GitHub Actions at 6AM after assembly.
Downloads the final video from Cloudinary and uploads it to Google Drive
so you can easily access, download, and manually post it.

Creates a clean folder structure in Drive:
  DopamineStudios/
    CH1-DopamineLoop/
      2025-04-01/
        final_video.mp4
        thumbnail.jpg
        seo.txt
    CH2-Finance/
      ...
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

CHANNEL_ID   = os.environ.get("CHANNEL_ID", "CH1")
DATE_STR     = datetime.now(timezone.utc).strftime("%Y-%m-%d")
DRIVE_ROOT   = "DopamineStudios"   # Root folder name in your Google Drive

CHANNEL_NAMES = {
    "CH1": "CH1-DopamineLoop",
    "CH2": "CH2-Finance",
    "CH3": "CH3-Conspiracy",
    "CH4": "CH4-Psychology",
    "CH5": "CH5-History",
}

# YouTube credentials (shared OAuth client)
CLIENT_ID     = os.environ.get("YOUTUBE_CLIENT_ID")
CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET")
REFRESH_TOKEN = os.environ.get(f"YOUTUBE_REFRESH_TOKEN_{CHANNEL_ID}")


def log(msg):
    print(f"[{CHANNEL_ID}][Drive] {msg}", flush=True)


def get_drive_service():
    """Build Google Drive service using YouTube OAuth credentials."""
    if not CLIENT_ID or not CLIENT_SECRET or not REFRESH_TOKEN:
        return None
    creds = Credentials(
        token=None,
        refresh_token=REFRESH_TOKEN,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=[
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/drive.file",
        ],
    )
    creds.refresh(Request())
    return build("drive", "v3", credentials=creds)


def find_or_create_folder(service, name: str, parent_id: str = None) -> str:
    """Find a Drive folder by name (and parent), create if not found."""
    query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"

    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])

    if files:
        return files[0]["id"]

    # Create the folder
    meta = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_id:
        meta["parents"] = [parent_id]

    folder = service.files().create(body=meta, fields="id").execute()
    log(f"Created Drive folder: {name}")
    return folder["id"]


def upload_file_to_drive(service, local_path: str, filename: str,
                          mime_type: str, folder_id: str) -> str:
    """Upload a local file to a specific Drive folder."""
    meta = {"name": filename, "parents": [folder_id]}
    media = MediaFileUpload(local_path, mimetype=mime_type, resumable=True)
    file = service.files().create(
        body=meta, media_body=media, fields="id,webViewLink"
    ).execute()
    return file.get("webViewLink", "")


def download_from_cloudinary(public_id: str, resource_type: str = "video") -> str | None:
    """Download a Cloudinary asset to a temp file. Returns local path or None."""
    try:
        result = cloudinary.api.resource(public_id, resource_type=resource_type)
        url = result["secure_url"]
        suffix = ".mp4" if resource_type == "video" else ".jpg"
        tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        resp = requests.get(url, stream=True, timeout=300)
        resp.raise_for_status()
        for chunk in resp.iter_content(chunk_size=8192):
            tmp.write(chunk)
        tmp.close()
        return tmp.name
    except Exception as e:
        log(f"[WARN] Could not download {public_id}: {e}")
        return None


def fetch_manifest() -> dict | None:
    public_id = f"dopamine-studios/{CHANNEL_ID}/manifests/{DATE_STR}"
    try:
        result = cloudinary.api.resource(public_id, resource_type="raw")
        resp = requests.get(result["secure_url"], timeout=10)
        return resp.json()
    except Exception as e:
        log(f"[ERROR] No manifest: {e}")
        return None


def main():
    log(f"Google Drive upload started — {DATE_STR}")

    manifest = fetch_manifest()
    if not manifest:
        log("[SKIP] No manifest found.")
        sys.exit(0)

    if manifest.get("status") not in ("assembled", "uploaded"):
        log(f"[SKIP] Manifest status: {manifest.get('status')} — not ready.")
        sys.exit(0)

    # Try to get Drive service
    service = get_drive_service()
    if not service:
        log("[SKIP] No Google credentials — Drive upload skipped.")
        log("  Add YOUTUBE_REFRESH_TOKEN_{CHANNEL_ID} to enable Drive upload.")
        sys.exit(0)

    # Build folder structure: DopamineStudios/CH1-DopamineLoop/2025-04-01/
    root_id    = find_or_create_folder(service, DRIVE_ROOT)
    ch_name    = CHANNEL_NAMES.get(CHANNEL_ID, CHANNEL_ID)
    ch_id      = find_or_create_folder(service, ch_name, root_id)
    date_id    = find_or_create_folder(service, DATE_STR, ch_id)

    # 1. Download and upload final video
    video_path = download_from_cloudinary(
        f"dopamine-studios/{CHANNEL_ID}/final/{DATE_STR}/video", "video"
    )
    if video_path:
        link = upload_file_to_drive(
            service, video_path, "final_video.mp4", "video/mp4", date_id
        )
        log(f"Video uploaded to Drive: {link}")
        os.remove(video_path)

    # 2. Download and upload thumbnail
    thumb_path = download_from_cloudinary(
        f"dopamine-studios/{CHANNEL_ID}/thumbnails/{DATE_STR}", "image"
    )
    if thumb_path:
        upload_file_to_drive(
            service, thumb_path, "thumbnail.jpg", "image/jpeg", date_id
        )
        log("Thumbnail uploaded to Drive.")
        os.remove(thumb_path)

    # 3. Create SEO text file and upload
    seo = manifest.get("seo", {})
    seo_content = f"""TITLE: {seo.get('title', '')}

DESCRIPTION:
{seo.get('description', '')}

TAGS: {', '.join(seo.get('tags', []))}

HASHTAGS: {' '.join(seo.get('hashtags', []))}

TOPIC: {manifest.get('topic', '')}
CHANNEL: {CHANNEL_ID}
DATE: {DATE_STR}
"""
    seo_tmp = tempfile.NamedTemporaryFile(
        suffix=".txt", mode="w", delete=False, encoding="utf-8"
    )
    seo_tmp.write(seo_content)
    seo_tmp.close()
    upload_file_to_drive(
        service, seo_tmp.name, "seo.txt", "text/plain", date_id
    )
    os.remove(seo_tmp.name)
    log("SEO file uploaded to Drive.")

    # 4. Update manifest with Drive folder info
    manifest["drive_folder_date_id"] = date_id
    manifest["drive_status"] = "uploaded"
    import base64
    manifest_str = json.dumps(manifest, indent=2)
    encoded = base64.b64encode(manifest_str.encode()).decode()
    cloudinary.uploader.upload(
        f"data:text/plain;base64,{encoded}",
        public_id=f"dopamine-studios/{CHANNEL_ID}/manifests/{DATE_STR}",
        resource_type="raw",
        overwrite=True,
    )

    log(f"\n[DONE] Everything for {CHANNEL_ID} is in your Google Drive.")
    log(f"  Folder: {DRIVE_ROOT}/{ch_name}/{DATE_STR}/")
    log("  Files: final_video.mp4, thumbnail.jpg, seo.txt")


if __name__ == "__main__":
    main()

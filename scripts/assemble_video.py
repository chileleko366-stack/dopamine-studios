"""
assemble_video.py
Runs inside GitHub Actions at 6AM.
Reads the render manifest from Cloudinary, downloads all clips,
assembles the final video using ffmpeg, uploads back to Cloudinary.

For celebrity channels: interleaves celebrity clips + mograph clips
For documentary channels: uses Edge TTS voiceover as audio spine
"""

import json
import os
import subprocess
import sys
import tempfile
import base64
from datetime import datetime, timezone
from pathlib import Path

import cloudinary
import cloudinary.uploader
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
WORK_DIR   = tempfile.mkdtemp(prefix=f"dopamine_{CHANNEL_ID}_")


def log(msg: str):
    print(f"[{CHANNEL_ID}] {msg}", flush=True)


def fetch_manifest() -> dict | None:
    """Download today's render manifest for this channel."""
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


def download_file(url: str, dest_path: str) -> bool:
    """Download a file from URL to local path."""
    try:
        resp = requests.get(url, timeout=60, stream=True)
        resp.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        log(f"  [ERROR] Download failed: {url} → {e}")
        return False


def fetch_celebrity_clip(cue: str, config: dict, dest_path: str) -> bool:
    """
    Try to get a celebrity clip from the Cloudinary asset library.
    Falls back to a mograph placeholder if not found.
    """
    search_prefix = f"dopamine-studios/{CHANNEL_ID}/assets/{cue.replace(' ', '_').lower()}"
    try:
        result = cloudinary.api.resources(
            type="upload",
            resource_type="video",
            prefix=search_prefix,
            max_results=1,
        )
        resources = result.get("resources", [])
        if resources:
            url = resources[0]["secure_url"]
            return download_file(url, dest_path)
    except Exception:
        pass
    log(f"  [WARN] No clip found for cue [{cue}] -- will use fallback mograph")
    return False


def generate_fallback_clip(line_text: str, dest_path: str, duration: int = 3):
    """Create a silent black frame clip as last-resort fallback using ffmpeg."""
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=black:size=1080x1920:duration={duration}:rate=24",
        "-f", "lavfi", "-i", f"aevalsrc=0:d={duration}",
        "-shortest",
        "-c:v", "libx264", "-c:a", "aac",
        dest_path,
    ]
    subprocess.run(cmd, capture_output=True, check=False)


def build_clip_list(manifest: dict, config: dict) -> list[str]:
    """
    Download/resolve all clips in order.
    Returns list of local file paths ready for concat.
    """
    clips_meta = manifest.get("clips", [])
    local_paths = []

    for i, clip in enumerate(clips_meta):
        clip_type  = clip.get("type")
        dest_path  = os.path.join(WORK_DIR, f"clip_{i:03d}.mp4")

        if clip_type == "mograph":
            url = clip.get("cloudinary_url")
            if url and download_file(url, dest_path):
                local_paths.append(dest_path)
            else:
                generate_fallback_clip(clip.get("line", ""), dest_path)
                local_paths.append(dest_path)

        elif clip_type == "celebrity_clip":
            cue = clip.get("cue", "")
            if not fetch_celebrity_clip(cue, config, dest_path):
                generate_fallback_clip(clip.get("line", ""), dest_path)
            local_paths.append(dest_path)

        elif clip_type == "render_failed":
            log(f"  Line {i}: render failed -- using black fallback")
            generate_fallback_clip(clip.get("line", ""), dest_path)
            local_paths.append(dest_path)

        log(f"  Resolved clip {i+1}/{len(clips_meta)}: {clip_type}")

    return local_paths


def concat_clips(local_paths: list[str], output_path: str) -> bool:
    """Concatenate all clips into one video using ffmpeg concat demuxer."""
    list_file = os.path.join(WORK_DIR, "concat_list.txt")
    with open(list_file, "w") as f:
        for p in local_paths:
            safe = p.replace("\\", "/")
            f.write(f"file '{safe}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_file,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-movflags", "+faststart",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log(f"[ERROR] ffmpeg concat failed:\n{result.stderr[-800:]}")
        return False
    return True


def add_voiceover(video_path: str, audio_path: str, output_path: str) -> bool:
    """
    Mix voiceover audio onto a silent/mute video.
    Used for documentary channels where Edge TTS generates the audio.
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log(f"[ERROR] Voiceover mix failed:\n{result.stderr[-500:]}")
        return False
    return True


def add_music(video_path: str, config: dict, output_path: str) -> bool:
    """
    Mix background music at low volume under the main audio.
    Music file must exist in Cloudinary asset library.
    """
    music_cue = config.get("sound", {}).get("music_mood", "")
    if not music_cue:
        # No music configured -- just copy
        import shutil
        shutil.copy2(video_path, output_path)
        return True

    music_prefix = f"dopamine-studios/{CHANNEL_ID}/assets/music/"
    try:
        result = cloudinary.api.resources(
            type="upload",
            resource_type="video",   # Cloudinary treats audio as video resource_type
            prefix=music_prefix,
            max_results=1,
        )
        resources = result.get("resources", [])
        if not resources:
            log("  [WARN] No music found in asset library -- skipping music mix")
            import shutil
            shutil.copy2(video_path, output_path)
            return True

        music_url = resources[0]["secure_url"]
        music_path = os.path.join(WORK_DIR, "music.mp3")
        download_file(music_url, music_path)

        # Mix: main audio at 100%, music at 8%
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", music_path,
            "-filter_complex",
            "[0:a]volume=1.0[main];[1:a]volume=0.08,aloop=loop=-1:size=2e+09[bg];[main][bg]amix=inputs=2:duration=first[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            log(f"  [WARN] Music mix failed -- using unmixed audio")
            import shutil
            shutil.copy2(video_path, output_path)
        return True
    except Exception as e:
        log(f"  [WARN] Music step skipped: {e}")
        import shutil
        shutil.copy2(video_path, output_path)
        return True


def upload_final_video(local_path: str, manifest: dict) -> str:
    """Upload final assembled video to Cloudinary."""
    public_id = f"dopamine-studios/{CHANNEL_ID}/final/{DATE_STR}/video"
    log(f"Uploading final video to Cloudinary...")
    result = cloudinary.uploader.upload(
        local_path,
        public_id=public_id,
        resource_type="video",
        overwrite=True,
        chunk_size=6000000,   # 6MB chunks for large files
    )
    url = result["secure_url"]
    log(f"Final video uploaded: {url}")

    # Save URL to manifest
    manifest["final_video_url"] = url
    manifest["status"] = "assembled"
    manifest_str = json.dumps(manifest, indent=2)
    encoded = base64.b64encode(manifest_str.encode()).decode()
    cloudinary.uploader.upload(
        f"data:text/plain;base64,{encoded}",
        public_id=f"dopamine-studios/{CHANNEL_ID}/manifests/{DATE_STR}",
        resource_type="raw",
        overwrite=True,
    )
    return url


def main():
    log(f"Assembly started -- {DATE_STR}")

    manifest = fetch_manifest()
    if not manifest:
        log("[ERROR] No manifest -- render PC may not have finished. Aborting.")
        sys.exit(1)

    if manifest.get("status") not in ("rendered", "assembled"):
        log(f"[ERROR] Manifest status is '{manifest.get('status')}' -- not ready. Aborting.")
        sys.exit(1)

    config = load_config()
    narrator_mode = manifest.get("narrator_mode", "off")

    log(f"Topic: {manifest.get('topic')}")
    log(f"Narrator mode: {narrator_mode}")
    log(f"Clips to resolve: {len(manifest.get('clips', []))}")

    # Step 1: Resolve all clips to local files
    local_clips = build_clip_list(manifest, config)
    if not local_clips:
        log("[ERROR] No clips resolved. Aborting.")
        sys.exit(1)

    # Step 2: Concatenate
    concat_path  = os.path.join(WORK_DIR, "concat.mp4")
    log(f"Concatenating {len(local_clips)} clips...")
    if not concat_clips(local_clips, concat_path):
        sys.exit(1)

    # Step 3: Add voiceover (documentary channels)
    if narrator_mode == "on":
        voice_public_id = f"dopamine-studios/{CHANNEL_ID}/voiceover/{DATE_STR}"
        try:
            voice_resource = cloudinary.api.resource(voice_public_id, resource_type="raw")
            voice_path = os.path.join(WORK_DIR, "voiceover.mp3")
            download_file(voice_resource["secure_url"], voice_path)
            voiced_path = os.path.join(WORK_DIR, "voiced.mp4")
            add_voiceover(concat_path, voice_path, voiced_path)
            concat_path = voiced_path
            log("Voiceover applied.")
        except Exception as e:
            log(f"[WARN] Voiceover not found: {e} -- continuing without")

    # Step 4: Add background music
    music_out = os.path.join(WORK_DIR, "with_music.mp4")
    add_music(concat_path, config, music_out)

    # Step 5: Upload final
    final_url = upload_final_video(music_out, manifest)
    log(f"\n[DONE] Final video ready: {final_url}")

    # Write final URL to env for next step (upload_youtube.py)
    with open(os.environ.get("GITHUB_ENV", "/dev/null"), "a") as f:
        f.write(f"FINAL_VIDEO_URL_{CHANNEL_ID}={final_url}\n")


if __name__ == "__main__":
    main()

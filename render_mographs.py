"""
render_mographs.py
Runs inside GitHub Actions — NO render PC needed for mographs.
Reads today's render job from Cloudinary, renders each mograph clip
using Remotion (React/Node.js), uploads back to Cloudinary.

Replaces ALL Blender mograph rendering.
The render PC (watcher.py) is now ONLY needed if you want to keep it —
but this script makes it completely optional.

Called by morning-assembly.yml before assemble_video.py
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
WORK_DIR   = tempfile.mkdtemp(prefix=f"remotion_{CHANNEL_ID}_")

# Channel color palettes
CHANNEL_PALETTES = {
    "CH1": {"primaryColor": "#e8ff47", "backgroundColor": "#0a0a0a"},
    "CH2": {"primaryColor": "#00d4aa", "backgroundColor": "#0d1117"},
    "CH3": {"primaryColor": "#ff3333", "backgroundColor": "#0d0d0d"},
    "CH4": {"primaryColor": "#7b61ff", "backgroundColor": "#0a0a1a"},
    "CH5": {"primaryColor": "#c8a24b", "backgroundColor": "#1a1008"},
}

# Map mograph template names to Remotion composition IDs
COMPOSITION_MAP = {
    "kinetic_quote":       "kinetic_quote",
    "particles_ascending": "particles_ascending",
    "data_graph_rise":     "data_graph_rise",
    "glitch_transition":   "glitch_transition",
    "crt_text_overlay":    "crt_text_overlay",
    "fire_ignite":         "fire_ignite",
    "chains_break":        "chains_break",
    "clock_dissolve":      "clock_dissolve",
    "maze_fragment":       "maze_fragment",
    "water_fill_screen":   "water_fill_screen",
    "map_zoom":            "map_zoom",
    "tv_intro":            "tv_intro",
    "end_screen":          "end_screen",
    # Fallback for any unknown template
    "default":             "kinetic_quote",
}


def log(msg: str):
    print(f"[{CHANNEL_ID}][Remotion] {msg}", flush=True)


def fetch_manifest() -> dict | None:
    public_id = f"dopamine-studios/{CHANNEL_ID}/manifests/{DATE_STR}"
    try:
        result = cloudinary.api.resource(public_id, resource_type="raw")
        resp = requests.get(result["secure_url"], timeout=15)
        return resp.json()
    except Exception as e:
        log(f"[ERROR] No manifest: {e}")
        return None


def install_remotion():
    """Install Node.js dependencies for Remotion in GitHub Actions."""
    remotion_dir = Path(__file__).parent.parent / "remotion"
    log("Installing Remotion dependencies...")
    result = subprocess.run(
        ["npm", "install", "--prefix", str(remotion_dir)],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        log(f"[ERROR] npm install failed: {result.stderr[-500:]}")
        return False
    log("Remotion installed.")
    return True


def render_clip(composition_id: str, props: dict, output_path: str, duration_frames: int = 72) -> bool:
    """
    Render a single Remotion composition to an MP4 file.
    """
    remotion_dir = Path(__file__).parent.parent / "remotion"
    props_json = json.dumps(props)

    cmd = [
        "npx", "remotion", "render",
        str(remotion_dir / "index.tsx"),
        composition_id,
        output_path,
        "--props", props_json,
        "--frames", f"0-{duration_frames - 1}",
        "--codec", "h264",
        "--output-file-name", output_path,
        "--log", "error",
    ]

    log(f"  Rendering {composition_id} → {Path(output_path).name}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            log(f"  [ERROR] Remotion failed: {result.stderr[-400:]}")
            return False
        if not os.path.exists(output_path):
            log(f"  [ERROR] Output not found: {output_path}")
            return False
        size_kb = os.path.getsize(output_path) // 1024
        log(f"  Rendered: {size_kb}KB")
        return True
    except subprocess.TimeoutExpired:
        log(f"  [ERROR] Remotion timed out on {composition_id}")
        return False


def upload_clip(local_path: str, line_index: int) -> str | None:
    """Upload rendered clip to Cloudinary."""
    public_id = f"dopamine-studios/{CHANNEL_ID}/rendered/{DATE_STR}/line{line_index:03d}"
    try:
        result = cloudinary.uploader.upload(
            local_path,
            public_id=public_id,
            resource_type="video",
            overwrite=True,
        )
        url = result["secure_url"]
        log(f"  Uploaded: {url}")
        return url
    except Exception as e:
        log(f"  [ERROR] Upload failed: {e}")
        return None
    finally:
        try:
            os.remove(local_path)
        except Exception:
            pass


def main():
    log(f"Mograph rendering started — {DATE_STR}")

    manifest = fetch_manifest()
    if not manifest:
        log("[SKIP] No manifest found.")
        sys.exit(0)

    if manifest.get("status") not in ("queued", "rendering"):
        log(f"[SKIP] Status is '{manifest.get('status')}' — skipping render.")
        sys.exit(0)

    # Install Remotion
    if not install_remotion():
        sys.exit(1)

    palette = CHANNEL_PALETTES.get(CHANNEL_ID, CHANNEL_PALETTES["CH1"])
    script_lines = manifest.get("script", {}).get("lines", [])
    rendered_clips = []

    for i, line_data in enumerate(script_lines):
        clip_cue = line_data.get("clip_cue", "no_clip")
        mograph  = line_data.get("mograph", {})

        # Celebrity clip — no render needed
        if clip_cue != "no_clip":
            log(f"  Line {i}: celebrity clip [{clip_cue}] — skipping")
            rendered_clips.append({
                "index": i, "type": "celebrity_clip",
                "cue": clip_cue, "line": line_data.get("line", ""),
            })
            continue

        template       = mograph.get("template", "kinetic_quote")
        composition_id = COMPOSITION_MAP.get(template, "kinetic_quote")
        intensity      = mograph.get("intensity", "medium")
        intensity_float = {"low": 0.3, "medium": 0.6, "high": 1.0}.get(intensity, 0.6)
        duration_frames = mograph.get("duration_frames", 72)

        # Build props for this composition
        props = {
            **palette,
            "intensity": intensity_float,
            "text": line_data.get("line", "")[:60].upper(),
            "label": mograph.get("theme", "").upper() or "NOW",
            "channelName": manifest.get("channel_name", "DOPAMINE"),
            "subscribeText": "SUBSCRIBE",
        }

        output_path = os.path.join(WORK_DIR, f"clip_{i:03d}_{template}.mp4")
        success = render_clip(composition_id, props, output_path, duration_frames)

        if not success:
            # Fallback to kinetic_quote
            log(f"  Falling back to kinetic_quote for line {i}")
            success = render_clip("kinetic_quote", props, output_path, 72)

        if success:
            cloud_url = upload_clip(output_path, i)
            rendered_clips.append({
                "index": i, "type": "mograph",
                "cloudinary_url": cloud_url, "line": line_data.get("line", ""),
            })
        else:
            rendered_clips.append({
                "index": i, "type": "render_failed", "line": line_data.get("line", ""),
            })

    # Write manifest with rendered clips
    manifest["clips"]  = rendered_clips
    manifest["status"] = "rendered"
    manifest_str = json.dumps(manifest, indent=2)
    encoded = base64.b64encode(manifest_str.encode()).decode()
    cloudinary.uploader.upload(
        f"data:text/plain;base64,{encoded}",
        public_id=f"dopamine-studios/{CHANNEL_ID}/manifests/{DATE_STR}",
        resource_type="raw",
        overwrite=True,
    )

    success_count = sum(1 for c in rendered_clips if c["type"] == "mograph")
    fail_count    = sum(1 for c in rendered_clips if c["type"] == "render_failed")
    log(f"\n[DONE] {success_count} mographs rendered, {fail_count} failed, manifest updated.")


if __name__ == "__main__":
    main()

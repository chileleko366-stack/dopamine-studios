"""
watcher.py
Runs 24/7 on the render PC (Windows 7/10).
Polls Cloudinary every 60 seconds for new render_job JSON files.
When a job appears, it:
  1. Downloads the job JSON
  2. For each mograph line: injects variables into the .blend template
  3. Fires Blender in --background headless mode
  4. Uploads the rendered clip directly to Cloudinary
  5. Marks job as done

HOW TO START ON THE RENDER PC:
  python watcher.py

HOW TO RUN ON STARTUP (Windows):
  Add a shortcut to this script in:
  shell:startup  (Win+R → type shell:startup)
  Or use Task Scheduler → trigger = "At log on"

REQUIREMENTS (install once):
  pip install cloudinary requests
"""

import json
import os
import subprocess
import sys
import time
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import cloudinary
import cloudinary.uploader
import cloudinary.api
import requests

# ── CONFIG — edit these once ─────────────────────────────────────────────────
CLOUDINARY_CLOUD_NAME = "YOUR_CLOUD_NAME"   # Replace
CLOUDINARY_API_KEY    = "YOUR_API_KEY"       # Replace
CLOUDINARY_API_SECRET = "YOUR_API_SECRET"    # Replace

BLENDER_PATH   = r"C:\Program Files\Blender Foundation\Blender 2.79\blender.exe"
TEMPLATES_DIR  = r"C:\DopamineStudios\BlenderTemplates"
TEMP_DIR       = r"C:\DopamineStudios\Temp"
POLL_INTERVAL  = 60       # seconds between Cloudinary polls
QUEUE_PREFIX   = "dopamine-studios/queue/render-job-"
DATE_STR       = datetime.now(timezone.utc).strftime("%Y-%m-%d")
# ─────────────────────────────────────────────────────────────────────────────

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
    secure=True,
)

os.makedirs(TEMP_DIR, exist_ok=True)


def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def fetch_queued_jobs() -> list[dict]:
    """Search Cloudinary for job files with status=queued in today's queue."""
    try:
        result = cloudinary.api.resources(
            type="upload",
            resource_type="raw",
            prefix=QUEUE_PREFIX,
            max_results=10,
        )
        jobs = []
        for r in result.get("resources", []):
            public_id = r["public_id"]
            if DATE_STR not in public_id:
                continue
            url = r["secure_url"]
            resp = requests.get(url, timeout=10)
            job = resp.json()
            if job.get("status") == "queued":
                jobs.append(job)
        return jobs
    except Exception as e:
        log(f"[ERROR] Polling failed: {e}")
        return []


def update_job_status(job: dict, status: str):
    """Re-upload the job JSON with updated status field."""
    import base64
    job["status"] = status
    job_str = json.dumps(job, indent=2)
    encoded = base64.b64encode(job_str.encode()).decode()
    public_id = f"{QUEUE_PREFIX}{job['channel_id']}-{DATE_STR}"
    cloudinary.uploader.upload(
        f"data:text/plain;base64,{encoded}",
        public_id=public_id,
        resource_type="raw",
        overwrite=True,
    )


def render_mograph_clip(line_data: dict, job: dict, line_index: int) -> str | None:
    """
    Renders one mograph clip via Blender headless.
    Returns local path of rendered .mp4, or None on failure.
    """
    mograph   = line_data.get("mograph", {})
    template  = mograph.get("template", "kinetic_quote")
    color     = mograph.get("primary_color", "#ffffff")
    intensity = mograph.get("intensity", "medium")
    frames    = mograph.get("duration_frames", 72)
    text      = line_data.get("line", "")[:80]      # max 80 chars on screen

    blend_file = os.path.join(TEMPLATES_DIR, f"{template}.blend")
    if not os.path.exists(blend_file):
        log(f"  [WARN] Template not found: {template}.blend — using kinetic_quote")
        blend_file = os.path.join(TEMPLATES_DIR, "kinetic_quote.blend")

    intensity_float = {"low": 0.3, "medium": 0.6, "high": 1.0}.get(intensity, 0.6)

    output_filename = f"{job['channel_id']}_line{line_index:03d}_{template}.mp4"
    output_path = os.path.join(TEMP_DIR, output_filename)

    # Python script injected into Blender at render time
    inject_script = f"""
import bpy, sys

# Inject variables
try:
    bpy.data.texts["render_vars"].body = ""
except:
    txt = bpy.data.texts.new("render_vars")

scene = bpy.context.scene
scene.frame_end = {frames}
scene.render.filepath = r"{output_path.replace(chr(92), chr(92)*2)}"
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.resolution_x = 1080
scene.render.resolution_y = 1920
scene.render.fps = 24

# Expose to node groups / drivers that reference these
bpy.app.driver_namespace["text_content"]   = "{text.replace(chr(34), chr(39))}"
bpy.app.driver_namespace["primary_color"]  = "{color}"
bpy.app.driver_namespace["intensity"]      = {intensity_float}
bpy.app.driver_namespace["duration_frames"] = {frames}

# Try to update text object if it exists
for obj in bpy.data.objects:
    if obj.type == 'FONT' and 'main_text' in obj.name.lower():
        obj.data.body = bpy.app.driver_namespace["text_content"]
        break

bpy.ops.render.render(animation=True)
"""

    script_path = os.path.join(TEMP_DIR, f"inject_{line_index}.py")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(inject_script)

    cmd = [
        BLENDER_PATH,
        "--background",
        blend_file,
        "--python", script_path,
    ]

    log(f"  Rendering: {template} (line {line_index}) — {frames} frames")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
        if result.returncode != 0:
            log(f"  [ERROR] Blender exit {result.returncode}")
            log(f"  STDERR: {result.stderr[-500:]}")
            return None
        if not os.path.exists(output_path):
            log(f"  [ERROR] Output not found: {output_path}")
            return None
        log(f"  Rendered: {output_filename}")
        return output_path
    except subprocess.TimeoutExpired:
        log(f"  [ERROR] Blender timeout on line {line_index}")
        return None
    except Exception as e:
        log(f"  [ERROR] {e}")
        return None
    finally:
        try:
            os.remove(script_path)
        except Exception:
            pass


def upload_clip_to_cloudinary(local_path: str, job: dict, line_index: int) -> str | None:
    """Upload rendered clip to Cloudinary and delete local file."""
    channel_id = job["channel_id"]
    public_id  = f"dopamine-studios/{channel_id}/rendered/{DATE_STR}/line{line_index:03d}"
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


def process_job(job: dict):
    channel_id = job["channel_id"]
    topic      = job.get("topic", "")
    log(f"\n{'='*50}")
    log(f"Processing job: {channel_id} — {topic}")
    log(f"{'='*50}")

    update_job_status(job, "rendering")

    script_lines = job.get("script", {}).get("lines", [])
    rendered_clips = []

    for i, line_data in enumerate(script_lines):
        clip_cue = line_data.get("clip_cue", "no_clip")

        # Only render mograph clips — real celebrity clips come from asset library
        if clip_cue != "no_clip":
            log(f"  Line {i}: real clip cue [{clip_cue}] — skipping Blender")
            rendered_clips.append({
                "index": i,
                "type": "celebrity_clip",
                "cue": clip_cue,
                "line": line_data.get("line", ""),
            })
            continue

        local_path = render_mograph_clip(line_data, job, i)
        if not local_path:
            log(f"  [WARN] Line {i} render failed — will use fallback in assembly")
            rendered_clips.append({
                "index": i,
                "type": "render_failed",
                "line": line_data.get("line", ""),
            })
            continue

        cloud_url = upload_clip_to_cloudinary(local_path, job, i)
        rendered_clips.append({
            "index": i,
            "type": "mograph",
            "cloudinary_url": cloud_url,
            "line": line_data.get("line", ""),
        })

    # Write render manifest back to Cloudinary for assembly step
    import base64
    manifest = {
        "job_id": job["job_id"],
        "channel_id": channel_id,
        "date": DATE_STR,
        "topic": topic,
        "seo": job.get("seo", {}),
        "narrator_mode": job.get("script", {}).get("narrator_mode", "off"),
        "voice": job.get("script", {}).get("voice", ""),
        "clips": rendered_clips,
        "status": "rendered",
    }
    manifest_str = json.dumps(manifest, indent=2)
    encoded = base64.b64encode(manifest_str.encode()).decode()
    cloudinary.uploader.upload(
        f"data:text/plain;base64,{encoded}",
        public_id=f"dopamine-studios/{channel_id}/manifests/{DATE_STR}",
        resource_type="raw",
        overwrite=True,
    )

    update_job_status(job, "rendered")
    log(f"\n[DONE] {channel_id} render complete. Manifest saved to Cloudinary.")


def main():
    log("DopamineStudios Watcher — started")
    log(f"Polling Cloudinary every {POLL_INTERVAL}s for date: {DATE_STR}")
    log(f"Blender: {BLENDER_PATH}")
    log(f"Templates: {TEMPLATES_DIR}\n")

    processed_jobs = set()

    while True:
        jobs = fetch_queued_jobs()

        for job in jobs:
            job_id = job.get("job_id")
            if job_id in processed_jobs:
                continue
            processed_jobs.add(job_id)
            try:
                process_job(job)
            except Exception as e:
                log(f"[FATAL] Job {job_id} crashed: {e}")
                update_job_status(job, "failed")

        if not jobs:
            log(f"No queued jobs. Next poll in {POLL_INTERVAL}s...")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()

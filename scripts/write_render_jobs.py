"""
write_render_jobs.py
Runs inside GitHub Actions at 11PM.
For each active channel tonight:
  1. Reads tonight's topic from Cloudinary
  2. Calls Claude API to generate full video script with mograph tags
  3. Writes one render_job.json per channel to Cloudinary /queue/
The render PC watcher picks these up and fires Blender.
"""

import base64
import json
import os
from datetime import datetime, timezone

import anthropic
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

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
DATE_STR = datetime.now(timezone.utc).strftime("%Y-%m-%d")

MOGRAPH_LOOKUP = {
    ("trapped", "high"): "prison_bars_closing",
    ("trapped", "low"): "shrinking_room",
    ("confinement", "high"): "prison_bars_closing",
    ("drowning", "any"): "water_fill_screen",
    ("rising", "any"): "particles_ascending",
    ("hope", "any"): "particles_ascending",
    ("growth", "any"): "particles_ascending",
    ("lost", "any"): "maze_fragment",
    ("time", "any"): "clock_dissolve",
    ("urgency", "any"): "clock_dissolve",
    ("passion", "any"): "fire_ignite",
    ("anger", "any"): "fire_ignite",
    ("freedom", "any"): "chains_break",
    ("success", "any"): "data_graph_rise",
    ("stats", "any"): "data_graph_rise",
    ("location", "any"): "map_zoom",
    ("global", "any"): "map_zoom",
    ("emphasis", "any"): "kinetic_quote",
}

def resolve_mograph(emotion: str, intensity: str) -> str:
    key = (emotion.lower(), intensity.lower())
    if key in MOGRAPH_LOOKUP:
        return MOGRAPH_LOOKUP[key]
    any_key = (emotion.lower(), "any")
    if any_key in MOGRAPH_LOOKUP:
        return MOGRAPH_LOOKUP[any_key]
    return "kinetic_quote"


def load_config(channel_id: str) -> dict:
    path = f"configs/channel-config-{channel_id.lower()}.json"
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def fetch_tonight_topics() -> dict:
    """Download tonight's topics JSON from Cloudinary."""
    try:
        result = cloudinary.api.resource(
            f"dopamine-studios/queue/tonight-topics-{DATE_STR}",
            resource_type="raw",
        )
        url = result["secure_url"]
        resp = requests.get(url, timeout=10)
        return resp.json()
    except Exception as e:
        print(f"[WARN] Could not fetch tonight topics: {e}")
        return {}


def generate_full_script(config: dict, topic: str) -> dict:
    """
    Calls Claude to generate the full video script with mograph cue tags.
    Returns structured dict with script lines + mograph assignments.
    """
    channel_name = config.get("channel_name", "")
    tone = config.get("script", {}).get("tone", "")
    hook = config.get("script", {}).get("hook", "")
    lesson_format = config.get("script", {}).get("lesson_format", "")
    narrator_mode = config.get("narrator", {}).get("mode", "off")
    voice = config.get("narrator", {}).get("voice", "en-US-GuyNeural")
    celebrities = config.get("script", {}).get("celebrities", "")
    palette = config.get("visual", {}).get("palette", {})
    primary_color = palette.get("primary", "#ffffff")
    is_documentary = narrator_mode == "on"

    script_type = "documentary narration" if is_documentary else "celebrity interview spine"

    prompt = f"""You are writing a YouTube video script for {channel_name}.
Topic: {topic}
Script type: {script_type}
Tone: {tone}
Hook formula: {hook}
Lesson format: {lesson_format}
{"Celebrity pool (pick one): " + celebrities if not is_documentary else ""}

Write the complete video script. Format EVERY line as JSON like this:
{{"line": "The script text here", "clip_cue": "celebrity_name_keyword OR no_clip", "mograph_tag": {{"emotion": "rising", "intensity": "high", "theme": "hope"}} }}

Rules:
- 60-90 seconds of spoken content for Shorts, 8-12 minutes for long-form
- Every line needs a clip_cue and mograph_tag
- clip_cue = "no_clip" when you want a mograph instead of a real clip
- mograph emotions must be from: trapped, confinement, drowning, rising, hope, growth, lost, time, urgency, passion, anger, freedom, success, stats, location, global, emphasis
- intensity = "high", "low", or "medium"
- Return ONLY a JSON array of line objects. No preamble, no markdown fences."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        script_lines = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"[WARN] Script JSON parse error: {e} -- using raw text fallback")
        script_lines = [{"line": raw, "clip_cue": "no_clip",
                         "mograph_tag": {"emotion": "emphasis", "intensity": "medium", "theme": "general"}}]

    resolved_lines = []
    for item in script_lines:
        tag = item.get("mograph_tag", {})
        emotion = tag.get("emotion", "emphasis")
        intensity = tag.get("intensity", "medium")
        blend_file = resolve_mograph(emotion, intensity)

        resolved_lines.append({
            "line": item.get("line", ""),
            "clip_cue": item.get("clip_cue", "no_clip"),
            "mograph": {
                "template": blend_file,
                "emotion": emotion,
                "intensity": intensity,
                "primary_color": primary_color,
                "duration_frames": 72,
            }
        })

    return {
        "topic": topic,
        "channel_id": config.get("channel_id"),
        "channel_name": channel_name,
        "narrator_mode": narrator_mode,
        "voice": voice,
        "primary_color": primary_color,
        "lines": resolved_lines,
        "date": DATE_STR,
    }


def generate_seo(config: dict, topic: str, script_lines: list) -> dict:
    """Generate title, description, tags, hashtags via Claude."""
    seo_config = config.get("seo", {})
    title_formula = seo_config.get("title_formula", "")
    desc_template = seo_config.get("description_template", "")
    hashtag_pool = seo_config.get("hashtag_pool", [])
    tags = seo_config.get("tags", [])
    upload_time = config.get("schedule", {}).get("upload_time", "08:00")

    script_snippet = " ".join([l["line"] for l in script_lines[:5]])

    prompt = f"""Generate YouTube SEO for this video.
Topic: {topic}
Script opening: {script_snippet}
Title formula: {title_formula}
Description template: {desc_template}
Available hashtags: {", ".join(hashtag_pool[:20])}
Available tags: {", ".join(tags[:30])}

Return ONLY a JSON object with keys: title, description, tags (list of 10), hashtags (list of 5).
No markdown, no preamble."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = message.content[0].text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        seo = json.loads(raw)
    except Exception:
        seo = {"title": topic, "description": "", "tags": tags[:10], "hashtags": hashtag_pool[:5]}

    seo["upload_time"] = upload_time
    return seo


def write_job_to_cloudinary(channel_id: str, job: dict):
    """Upload the render job JSON to Cloudinary queue folder."""
    job_str = json.dumps(job, indent=2)
    encoded = base64.b64encode(job_str.encode()).decode()
    public_id = f"dopamine-studios/queue/render-job-{channel_id}-{DATE_STR}"

    result = cloudinary.uploader.upload(
        f"data:text/plain;base64,{encoded}",
        public_id=public_id,
        resource_type="raw",
        overwrite=True,
    )
    print(f"[{channel_id}] Job written to Cloudinary: {result['secure_url']}")
    return result["secure_url"]


def main():
    tonight_topics = fetch_tonight_topics()

    if not tonight_topics:
        print("[WARN] No topics found. Did generate_topics.py run?")
        return

    for channel_id, topic_data in tonight_topics.items():
        if topic_data.get("status") != "pending":
            print(f"[{channel_id}] Status is '{topic_data.get('status')}' -- skipping.")
            continue

        config = load_config(channel_id)
        if not config:
            print(f"[{channel_id}] No config found -- skipping.")
            continue

        topic = topic_data["topic"]
        print(f"\n[{channel_id}] Generating script for: {topic}")

        script_data = generate_full_script(config, topic)
        seo_data = generate_seo(config, topic, script_data["lines"])

        render_job = {
            "job_id": f"{channel_id}-{DATE_STR}",
            "channel_id": channel_id,
            "date": DATE_STR,
            "status": "queued",
            "topic": topic,
            "script": script_data,
            "seo": seo_data,
            "cloudinary_output_folder": f"dopamine-studios/{channel_id}/rendered/{DATE_STR}",
            "final_video_path": f"dopamine-studios/{channel_id}/final/{DATE_STR}",
        }

        write_job_to_cloudinary(channel_id, render_job)
        print(f"[{channel_id}] Render job queued.")

    print("\n[DONE] All render jobs written to Cloudinary queue.")


if __name__ == "__main__":
    main()

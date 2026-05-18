"""
generate_topics.py
Generates tonight's video topic per channel and saves to Cloudinary.
FORCE_RUN=true bypasses schedule check so manual triggers always work.
"""

import json
import os
import base64
from datetime import datetime, timezone

import cloudinary
import cloudinary.uploader
import requests
from claude_client import generate

cloudinary.config(
    cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
    api_key=os.environ["CLOUDINARY_API_KEY"],
    api_secret=os.environ["CLOUDINARY_API_SECRET"],
    secure=True,
)

CHANNEL_IDS = ["CH1", "CH2", "CH3", "CH4", "CH5"]
CONFIGS_DIR = "configs"
CHANNEL_OVERRIDE = os.environ.get("CHANNEL_OVERRIDE", "ALL").strip().upper()
TOPIC_OVERRIDE = os.environ.get("TOPIC_OVERRIDE", "").strip()
FORCE_RUN = os.environ.get("FORCE_RUN", "false").lower() == "true"


def load_config(channel_id):
    path = os.path.join(CONFIGS_DIR, f"channel-config-{channel_id.lower()}.json")
    if not os.path.exists(path):
        print(f"[WARN] No config for {channel_id}")
        return None
    with open(path) as f:
        return json.load(f)


def should_run(config):
    if TOPIC_OVERRIDE or FORCE_RUN:
        return True
    today = datetime.now().strftime("%a").upper()[:3]
    return today in config.get("schedule", {}).get("upload_days", [])


def generate_topic(config):
    if TOPIC_OVERRIDE:
        return TOPIC_OVERRIDE

    channel_name = config.get("channel_name", "Unknown")
    mission = config.get("identity", {}).get("mission", "")
    tone = config.get("script", {}).get("tone", "")[:600]
    forbidden = config.get("identity", {}).get("forbidden", "")
    forbidden_words = config.get("script", {}).get("forbidden_words", "")
    power_words = config.get("script", {}).get("power_words", "")
    hook = config.get("script", {}).get("hook", "")[:300]
    subject_pool = (
        config.get("script", {}).get("celebrities") or
        config.get("script", {}).get("subjects") or
        config.get("script", {}).get("researchers_and_studies") or
        config.get("script", {}).get("subject_areas") or ""
    )

    system = f"""You are the editorial director of "{channel_name}".
MISSION: {mission}
TONE: {tone}
SUBJECT POOL: {str(subject_pool)[:600]}
HOOK FORMULA: {hook}
FORBIDDEN TOPICS: {forbidden}
FORBIDDEN WORDS: {forbidden_words}
POWER WORDS: {power_words}
Return ONLY the topic string. No quotes, no preamble."""

    return generate(
        system=system,
        user="Generate one video topic for tonight.",
        max_tokens=200,
        temperature=0.85,
    ).strip().strip('"').strip("'")


def main():
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    tonight_topics = {}

    channels = CHANNEL_IDS if CHANNEL_OVERRIDE == "ALL" else [CHANNEL_OVERRIDE]

    for ch in channels:
        config = load_config(ch)
        if not config or not should_run(config):
            print(f"[{ch}] Skipping (not scheduled or no config)")
            continue

        print(f"[{ch}] Generating topic...")
        try:
            topic = generate_topic(config)
            print(f"[{ch}] Topic: {topic}")
            tonight_topics[ch] = {
                "channel_name": config.get("channel_name"),
                "topic": topic,
                "date": date_str,
                "status": "pending",
                "narrator_mode": config.get("narrator", {}).get("mode", "off"),
                "voice": config.get("narrator", {}).get("voice", "en-US-GuyNeural"),
                "schedule": config.get("schedule", {}),
            }
        except Exception as e:
            print(f"[{ch}] ERROR: {e}")

    if not tonight_topics:
        print("[DONE] No topics generated.")
        return

    topics_str = json.dumps(tonight_topics, indent=2)
    result = cloudinary.uploader.upload(
        "data:text/plain;base64," + base64.b64encode(topics_str.encode()).decode(),
        public_id=f"dopamine-studios/queue/tonight-topics-{date_str}",
        resource_type="raw",
        overwrite=True,
    )
    print(f"[DONE] Topics uploaded: {result.get('secure_url')}")
    print(json.dumps(tonight_topics, indent=2))


if __name__ == "__main__":
    main()

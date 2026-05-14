"""
generate_topics.py
Runs inside GitHub Actions at 10PM.
Reads all channel-config.json files, calls Claude to generate tonight's
video topic for each channel, saves to Cloudinary.

Schedule logic:
- If FORCE_RUN=true AND CHANNEL_OVERRIDE=ALL → generate for all channels
- If FORCE_RUN=true AND CHANNEL_OVERRIDE=CH4 → always generate for CH4
  (bypasses the schedule check so manual triggers always work)
- If FORCE_RUN=false → only generate for channels scheduled today
"""

import json
import os
import base64
from datetime import datetime, timezone

import cloudinary
import cloudinary.uploader
import cloudinary.api
import requests

from claude_client import generate

cloudinary.config(
    cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
    api_key=os.environ["CLOUDINARY_API_KEY"],
    api_secret=os.environ["CLOUDINARY_API_SECRET"],
    secure=True,
)

CHANNEL_IDS      = ["CH1", "CH2", "CH3", "CH4", "CH5"]
CONFIGS_DIR      = "configs"
CHANNEL_OVERRIDE = os.environ.get("CHANNEL_OVERRIDE", "ALL").strip().upper()
TOPIC_OVERRIDE   = os.environ.get("TOPIC_OVERRIDE", "").strip()
FORCE_RUN        = os.environ.get("FORCE_RUN", "false").lower() == "true"


def load_config(channel_id: str) -> dict:
    path = os.path.join(CONFIGS_DIR, f"channel-config-{channel_id.lower()}.json")
    if not os.path.exists(path):
        print(f"[WARN] No config found for {channel_id}, skipping.")
        return None
    with open(path) as f:
        return json.load(f)


def channel_active_today(config: dict) -> bool:
    today = datetime.now().strftime("%a").upper()[:3]
    upload_days = config.get("schedule", {}).get("upload_days", [])
    return today in upload_days


def should_run(config: dict, channel_id: str) -> bool:
    """
    Determine whether to generate a topic for this channel.
    FORCE_RUN bypasses schedule check entirely when a specific channel is
    requested, so manual workflow triggers always work.
    """
    if TOPIC_OVERRIDE:
        return True
    if FORCE_RUN:
        # Manual trigger: always run the requested channel(s)
        return True
    # Cron trigger: respect the schedule
    return channel_active_today(config)


def generate_topic(config: dict) -> str:
    if TOPIC_OVERRIDE and (
        CHANNEL_OVERRIDE == "ALL" or CHANNEL_OVERRIDE == config.get("channel_id")
    ):
        return TOPIC_OVERRIDE

    channel_name   = config.get("channel_name", "Unknown")
    mission        = config.get("identity", {}).get("mission", "")
    tone           = config.get("script", {}).get("tone", "")
    forbidden      = config.get("identity", {}).get("forbidden", "")
    hook_formula   = config.get("script", {}).get("hook", "")
    power_words    = config.get("script", {}).get("power_words", "")
    forbidden_words = config.get("script", {}).get("forbidden_words", "")

    subject_pool = (
        config.get("script", {}).get("celebrities")
        or config.get("script", {}).get("subjects")
        or config.get("script", {}).get("researchers_and_studies")
        or config.get("script", {}).get("subject_areas")
        or ""
    )

    system_prompt = f"""You are the editorial director of the YouTube channel "{channel_name}".

CHANNEL MISSION:
{mission}

EDITORIAL TONE:
{tone[:600]}

SUBJECT POOL (pick one if relevant):
{str(subject_pool)[:600]}

HOOK FORMULA:
{hook_formula[:300]}

FORBIDDEN TOPICS: {forbidden}
FORBIDDEN WORDS IN TITLES: {forbidden_words}
POWER WORDS: {power_words}

CRITICAL: Return ONLY the topic string. No quotes, no preamble, no explanation.
Be specific, scroll-stopping, and faithful to the channel's editorial tone.
"""
    return generate(
        system=system_prompt,
        user="Generate one video topic for tonight.",
        max_tokens=200,
        temperature=0.85,
    ).strip().strip('"').strip("'")


def main():
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    tonight_topics = {}

    channels_to_run = (
        CHANNEL_IDS if CHANNEL_OVERRIDE == "ALL" else [CHANNEL_OVERRIDE]
    )

    for channel_id in channels_to_run:
        config = load_config(channel_id)
        if not config:
            continue

        if not should_run(config, channel_id):
            print(f"[{channel_id}] Not scheduled today -- skipping. (Set FORCE_RUN=true to override)")
            continue

        print(f"[{channel_id}] Generating topic...")
        try:
            topic = generate_topic(config)
        except Exception as e:
            print(f"[{channel_id}] [ERROR] Topic generation failed: {e}")
            continue

        print(f"[{channel_id}] Topic: {topic}")
        tonight_topics[channel_id] = {
            "channel_name": config.get("channel_name"),
            "topic": topic,
            "date": date_str,
            "status": "pending",
            "narrator_mode": config.get("narrator", {}).get("mode", "off"),
            "voice": config.get("narrator", {}).get("voice", "en-US-GuyNeural"),
            "schedule": config.get("schedule", {}),
        }

    if not tonight_topics:
        print("[DONE] No channels generated topics. Exiting.")
        return

    topics_str = json.dumps(tonight_topics, indent=2)
    result = cloudinary.uploader.upload(
        "data:text/plain;base64," + base64.b64encode(topics_str.encode()).decode(),
        public_id=f"dopamine-studios/queue/tonight-topics-{date_str}",
        resource_type="raw",
        overwrite=True,
    )
    print(f"[OK] Topics saved: {result['secure_url']}")
    print(f"[DONE] Generated topics for: {list(tonight_topics.keys())}")


if __name__ == "__main__":
    main()

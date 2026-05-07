"""
generate_topics.py
Runs inside GitHub Actions at 10PM.
Reads all channel-config.json files, calls Claude API to generate
tonight's video topic for each channel, saves as tonight_topics.json
to Cloudinary and sets GitHub Actions output.
"""

import json
import os
import sys
from datetime import datetime, timezone
import anthropic
import cloudinary
import cloudinary.uploader
import cloudinary.api

cloudinary.config(
    cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
    api_key=os.environ["CLOUDINARY_API_KEY"],
    api_secret=os.environ["CLOUDINARY_API_SECRET"],
    secure=True,
)

CHANNEL_IDS = ["CH1", "CH2", "CH3", "CH4", "CH5"]
CONFIGS_DIR = "configs"
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

CHANNEL_OVERRIDE = os.environ.get("CHANNEL_OVERRIDE", "ALL")
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

def generate_topic(config: dict) -> str:
    channel_name = config.get("channel_name", "Unknown")
    mission = config.get("identity", {}).get("mission", "")
    tone = config.get("script", {}).get("tone", "")
    forbidden = config.get("identity", {}).get("forbidden", "")
    celebrities = config.get("script", {}).get("celebrities", "")
    hook_formula = config.get("script", {}).get("hook", "")
    power_words = config.get("script", {}).get("power_words", "")

    if TOPIC_OVERRIDE and (CHANNEL_OVERRIDE == "ALL" or CHANNEL_OVERRIDE == config.get("channel_id")):
        return TOPIC_OVERRIDE

    prompt = f"""You are generating ONE video topic for {channel_name}.

Channel mission: {mission}
Script tone: {tone[:300]}
Forbidden topics: {forbidden}
Celebrity pool (choose one if relevant): {celebrities[:400]}
Power words to favour: {power_words}
Hook formula: {hook_formula[:200]}

Generate a single compelling YouTube video topic for tonight.
Return ONLY the topic string -- no explanation, no quotes, no formatting.
Make it specific, emotional, and scroll-stopping.
Example format: "Why Kanye West's loneliness destroyed him before it saved him"
"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text.strip().strip('"').strip("'")

def main():
    tonight_topics = {}
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    channels_to_run = CHANNEL_IDS if CHANNEL_OVERRIDE == "ALL" else [CHANNEL_OVERRIDE]

    for channel_id in channels_to_run:
        config = load_config(channel_id)
        if not config:
            continue

        if not channel_active_today(config) and not FORCE_RUN and not TOPIC_OVERRIDE:
            print(f"[{channel_id}] Not scheduled today -- skipping.")
            continue

        print(f"[{channel_id}] Generating topic...")
        topic = generate_topic(config)
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

    topics_str = json.dumps(tonight_topics, indent=2)
    result = cloudinary.uploader.upload(
        "data:text/plain;base64," + __import__("base64").b64encode(topics_str.encode()).decode(),
        public_id=f"dopamine-studios/queue/tonight-topics-{date_str}",
        resource_type="raw",
        overwrite=True,
    )
    print(f"[OK] Topics saved to Cloudinary: {result['secure_url']}")

    safe_json = topics_str.replace("%", "%25").replace("\n", "%0A").replace("\r", "%0D")
    print(f"topics_json={safe_json}", file=open(os.environ.get("GITHUB_OUTPUT", "/dev/stdout"), "a"))
    print(f"\n[DONE] Generated topics for {len(tonight_topics)} channel(s).")

if __name__ == "__main__":
    main()

"""
telegram_notify.py
Handles all Telegram messages the pipeline sends to your Android phone.
Four modes: preview, render_start, success, morning_summary

Setup:
  1. Create a bot via @BotFather on Telegram → get BOT_TOKEN
  2. Message your bot once, then visit:
     https://api.telegram.org/bot<TOKEN>/getUpdates
     to find your CHAT_ID
  3. Add both to GitHub Actions secrets
"""

import argparse
import json
import os
import sys
import requests
from datetime import datetime, timezone

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

CHANNEL_NAMES = {
    "CH1": "DopamineLoop",
    "CH2": "Finance",
    "CH3": "Conspiracy",
    "CH4": "Psychology",
    "CH5": "History",
}

CHANNEL_EMOJI = {
    "CH1": "⚡",
    "CH2": "💰",
    "CH3": "🔍",
    "CH4": "🧠",
    "CH5": "📜",
}


def send_message(text: str, parse_mode: str = "HTML") -> dict:
    resp = requests.post(
        f"{BASE_URL}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text, "parse_mode": parse_mode},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def mode_preview():
    """10PM — shows tonight's auto-topics with override instructions."""
    raw = os.environ.get("TOPICS_JSON", "{}")
    topics = json.loads(raw) if raw else {}

    if not topics:
        send_message("⚠️ <b>DopamineStudios</b>\nNo channels scheduled tonight.")
        return

    lines = ["🎬 <b>Tonight's topics — approve or override by 11PM</b>\n"]
    for ch_id, data in topics.items():
        emoji = CHANNEL_EMOJI.get(ch_id, "▶️")
        name = CHANNEL_NAMES.get(ch_id, ch_id)
        topic = data.get("topic", "—")
        lines.append(f"{emoji} <b>{name}</b>\n<i>{topic}</i>\n")

    lines.append("─────────────────")
    lines.append("To override: reply with <code>OVERRIDE CH1 Your new topic here</code>")
    lines.append("To approve all: do nothing — render fires at 11PM automatically.")

    send_message("\n".join(lines))
    print("[OK] Preview notification sent.")


def mode_render_start():
    """11PM — tells you the render PC should be waking up."""
    now = datetime.now(timezone.utc).strftime("%H:%M UTC")
    send_message(
        f"🖥️ <b>Render jobs queued — {now}</b>\n\n"
        "Blender watcher should be picking up jobs now.\n"
        "Make sure the PC is on. Renders run overnight.\n\n"
        "✅ Nothing more needed from you tonight."
    )
    print("[OK] Render start notification sent.")


def mode_success():
    """Morning — confirms a specific channel uploaded successfully."""
    channel_id = os.environ.get("CHANNEL_ID", "Unknown")
    name = CHANNEL_NAMES.get(channel_id, channel_id)
    emoji = CHANNEL_EMOJI.get(channel_id, "✅")
    send_message(
        f"{emoji} <b>{name}</b> uploaded successfully!\n"
        f"Video is live and scheduled on YouTube."
    )
    print(f"[OK] Success notification sent for {channel_id}.")


def mode_morning_summary():
    """6AM — overall pipeline result summary."""
    status = os.environ.get("PIPELINE_STATUS", "unknown")
    icon = "✅" if status == "success" else "⚠️" if status == "failure" else "❓"
    date_str = datetime.now(timezone.utc).strftime("%d %b %Y")

    msg = (
        f"{icon} <b>DopamineStudios — {date_str}</b>\n"
        f"Pipeline status: <code>{status}</code>\n\n"
        "Check the GitHub Actions tab for per-channel details:\n"
        "https://github.com/YOUR_USERNAME/dopamine-studios/actions"
    )
    send_message(msg)
    print("[OK] Morning summary sent.")


def mode_error(message: str):
    """Send an error alert — called by other scripts on failure."""
    send_message(f"🚨 <b>Pipeline error</b>\n\n<code>{message[:800]}</code>")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True,
                        choices=["preview", "render_start", "success", "morning_summary", "error"])
    parser.add_argument("--message", default="", help="Used with --mode error")
    args = parser.parse_args()

    if args.mode == "preview":
        mode_preview()
    elif args.mode == "render_start":
        mode_render_start()
    elif args.mode == "success":
        mode_success()
    elif args.mode == "morning_summary":
        mode_morning_summary()
    elif args.mode == "error":
        mode_error(args.message or "Unknown error")

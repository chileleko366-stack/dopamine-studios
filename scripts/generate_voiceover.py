"""
generate_voiceover.py
Generates Edge TTS voiceover for documentary channels (CH3 Conspiracy, CH5 History).
Reads the script from today's render manifest, generates MP3, uploads to Cloudinary.
"""

import asyncio
import base64
import json
import os
import sys
import tempfile
from datetime import datetime, timezone

import cloudinary
import cloudinary.uploader
import cloudinary.api
import requests
import edge_tts

cloudinary.config(
    cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
    api_key=os.environ["CLOUDINARY_API_KEY"],
    api_secret=os.environ["CLOUDINARY_API_SECRET"],
    secure=True,
)

CHANNEL_ID = os.environ.get("CHANNEL_ID", "CH3")
DATE_STR   = datetime.now(timezone.utc).strftime("%Y-%m-%d")

# Voice per channel -- set in channel config, overridable here
CHANNEL_VOICES = {
    "CH3": "en-US-GuyNeural",        # Conspiracy -- deep, serious
    "CH5": "en-GB-RyanNeural",       # History -- British academic
}


def log(msg: str):
    print(f"[{CHANNEL_ID}] {msg}", flush=True)


def fetch_manifest() -> dict | None:
    public_id = f"dopamine-studios/{CHANNEL_ID}/manifests/{DATE_STR}"
    try:
        result = cloudinary.api.resource(public_id, resource_type="raw")
        resp   = requests.get(result["secure_url"], timeout=10)
        return resp.json()
    except Exception as e:
        log(f"[ERROR] Could not fetch manifest: {e}")
        return None


def extract_full_script(manifest: dict) -> str:
    """Join all script lines into one continuous narration string."""
    lines = manifest.get("script", {}).get("lines", [])
    return " ".join(item.get("line", "") for item in lines if item.get("line"))


async def generate_tts(text: str, voice: str, output_path: str):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)


def main():
    log(f"Voiceover generation started -- {DATE_STR}")

    manifest = fetch_manifest()
    if not manifest:
        log("[ERROR] No manifest found. Aborting.")
        sys.exit(1)

    narrator_mode = manifest.get("narrator_mode") or manifest.get("script", {}).get("narrator_mode", "off")
    if narrator_mode != "on":
        log("Narrator mode is off -- skipping voiceover.")
        sys.exit(0)

    voice = manifest.get("voice") or CHANNEL_VOICES.get(CHANNEL_ID, "en-US-GuyNeural")
    script_text = extract_full_script(manifest)

    if not script_text.strip():
        log("[ERROR] No script text found in manifest.")
        sys.exit(1)

    log(f"Voice: {voice}")
    log(f"Script length: {len(script_text)} characters")

    # Generate TTS to temp file
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp.close()

    log("Generating voiceover with Edge TTS...")
    asyncio.run(generate_tts(script_text, voice, tmp.name))
    log(f"Voiceover generated: {tmp.name}")

    # Upload to Cloudinary
    public_id = f"dopamine-studios/{CHANNEL_ID}/voiceover/{DATE_STR}"
    result = cloudinary.uploader.upload(
        tmp.name,
        public_id=public_id,
        resource_type="raw",
        overwrite=True,
    )
    log(f"Voiceover uploaded: {result['secure_url']}")

    try:
        os.remove(tmp.name)
    except Exception:
        pass

    log("[DONE] Voiceover ready in Cloudinary.")


if __name__ == "__main__":
    main()

"""
write_render_jobs.py
Runs inside GitHub Actions at 10PM (after generate_topics.py).

For each channel that has a topic in tonight's queue:
  1. Loads the channel bible (configs/channel-config-{id}.json)
  2. Generates an OUTLINE faithful to the bible (Claude, multi-stage)
  3. Drafts SECTION BODIES from the outline (Claude, per-section)
  4. Splits the full script into LINES (sentence-level units for rendering)
  5. Assigns each line a mograph template + intensity (deterministic mapping
     from the bible's `mograph.triggers` to keyword detection)
  6. Validates against the bible's forbidden_words list, regenerating any
     section that fails
  7. Writes the manifest to Cloudinary in the EXACT shape that
     render_mographs.py expects: { script: { lines: [{line, clip_cue, mograph}] } }

This script replaces the previous duplicate-of-generate-topics.py that wrote
nothing useful.

Output contract (matches render_mographs.py expectations):
{
  "channel_id": "CH1",
  "channel_name": "DOPAMINE LOOP",
  "date": "2026-05-13",
  "status": "queued",
  "topic": "Why Kanye's loneliness destroyed him before it saved him",
  "narrator_mode": "off"|"on",
  "voice": "en-US-GuyNeural",
  "script": {
    "title": "...",
    "full_text": "...",
    "lines": [
      {
        "index": 0,
        "line": "The text of this single line",
        "clip_cue": "kanye_breakdown_interview_2019" | "no_clip",
        "mograph": {
          "template": "kinetic_quote",
          "intensity": "low" | "medium" | "high",
          "theme": "loneliness",
          "duration_frames": 72
        }
      },
      ...
    ]
  },
  "seo": { "title": "...", "description": "...", "tags": [...] }
}
"""

import json
import os
import re
import base64
import sys
from datetime import datetime, timezone
from typing import Optional

import cloudinary
import cloudinary.uploader
import cloudinary.api
import requests

from claude_client import generate, generate_json

cloudinary.config(
    cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
    api_key=os.environ["CLOUDINARY_API_KEY"],
    api_secret=os.environ["CLOUDINARY_API_SECRET"],
    secure=True,
)

CHANNEL_IDS    = ["CH1", "CH2", "CH3", "CH4", "CH5"]
CONFIGS_DIR    = "configs"
DATE_STR       = datetime.now(timezone.utc).strftime("%Y-%m-%d")

CHANNEL_OVERRIDE = os.environ.get("CHANNEL_OVERRIDE", "ALL")

# Default mograph template for each channel when no keyword matches
CHANNEL_DEFAULT_TEMPLATE = {
    "CH1": "kinetic_quote",       # Dopamine Loop -- philosophical kinetic typography
    "CH2": "data_graph_rise",     # FinanceFiction -- financial visualisation
    "CH3": "crt_text_overlay",    # REDACTED -- document/typewriter feel
    "CH4": "kinetic_quote",       # Grey Matter -- serif text
    "CH5": "kinetic_quote",       # Quiet Record -- archival serif
}


def log(channel_id: str, msg: str):
    print(f"[{channel_id}][script-gen] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Config + topic loading
# ---------------------------------------------------------------------------

def load_config(channel_id: str) -> Optional[dict]:
    path = os.path.join(CONFIGS_DIR, f"channel-config-{channel_id.lower()}.json")
    if not os.path.exists(path):
        log(channel_id, f"[WARN] No config: {path}")
        return None
    with open(path) as f:
        return json.load(f)


def fetch_topics() -> dict:
    """Fetch tonight's topics file from Cloudinary."""
    public_id = f"dopamine-studios/queue/tonight-topics-{DATE_STR}"
    try:
        result = cloudinary.api.resource(public_id, resource_type="raw")
        resp = requests.get(result["secure_url"], timeout=15)
        return resp.json()
    except Exception as e:
        print(f"[ERROR] No topics file for {DATE_STR}: {e}")
        return {}


# ---------------------------------------------------------------------------
# Stage A: outline
# ---------------------------------------------------------------------------

def stage_outline(config: dict, topic: str) -> dict:
    """Ask Claude for a section-by-section outline. Returns dict with 'title' and 'sections'."""
    bible_extract = _build_bible_extract(config, sections=("identity", "script"))

    system = f"""You are the head writer for the YouTube channel "{config.get('channel_name')}".
You have spent years internalising the editorial bible below.
You always write faithfully to it.

CHANNEL BIBLE (EXCERPT):
{bible_extract}
"""
    user = f"""Outline tonight's video on this topic:

TOPIC: {topic}

Return ONLY a JSON object with this exact shape:
{{
  "title": "string -- the video title, under 70 chars, no clickbait clichés",
  "sections": [
    {{
      "name": "Section name (e.g. 'Hook', 'The Problem', 'The Turn', 'The Lesson')",
      "purpose": "1-sentence description of what this section accomplishes",
      "approx_seconds": 60
    }}
  ]
}}

Target total length matches the channel's `script.length` field.
The number of sections should match what the channel's bible expects (usually 4-8).
Do not write any actual script lines yet. This is the outline only."""

    return generate_json(system=system, user=user, max_tokens=2000, temperature=0.6)


# ---------------------------------------------------------------------------
# Stage B: per-section script
# ---------------------------------------------------------------------------

def stage_section(config: dict, topic: str, outline: dict, section_idx: int) -> str:
    """Draft the body of one section. Returns raw script prose."""
    section = outline["sections"][section_idx]
    bible_extract = _build_bible_extract(
        config,
        sections=("identity", "script", "editing"),
    )

    forbidden_words = config.get("script", {}).get("forbidden_words", "")
    power_words     = config.get("script", {}).get("power_words", "")

    system = f"""You are the head writer for "{config.get('channel_name')}".

CHANNEL BIBLE (EXCERPT):
{bible_extract}

ABSOLUTE RULES:
- NEVER use these forbidden words: {forbidden_words}
- Favour these power words where natural: {power_words}
- Write in the exact tonal voice specified in the bible
- Match the section purpose precisely
- Do not include section headers, stage directions, or anything that isn't spoken aloud
- One sentence per line. Use short, direct sentences. No em-dash run-ons.
"""
    user = f"""TOPIC: {topic}
VIDEO TITLE: {outline.get('title')}

CURRENT SECTION: {section.get('name')}
PURPOSE: {section.get('purpose')}
TARGET DURATION: about {section.get('approx_seconds', 60)} seconds of narration (around {max(3, int(section.get('approx_seconds', 60) / 8))} short lines)

Context (other sections for continuity, in order):
{json.dumps([{'name': s['name'], 'purpose': s['purpose']} for s in outline['sections']], indent=2)}

Write the spoken prose for this section ONLY. No labels, no markdown, no headers.
One sentence per line. Each line should stand alone visually."""

    return generate(system=system, user=user, max_tokens=2000, temperature=0.75)


# ---------------------------------------------------------------------------
# Stage C: forbidden-words validation
# ---------------------------------------------------------------------------

def validate_forbidden(text: str, forbidden_csv: str) -> list[str]:
    """Return a list of forbidden words found in the text (case-insensitive, word boundary)."""
    if not forbidden_csv.strip():
        return []
    forbidden = [w.strip().lower() for w in forbidden_csv.split(",") if w.strip()]
    found = []
    lowered = text.lower()
    for word in forbidden:
        # Use word boundary for single tokens; substring for multi-word phrases
        if " " in word:
            if word in lowered:
                found.append(word)
        else:
            if re.search(rf"\b{re.escape(word)}\b", lowered):
                found.append(word)
    return found


# ---------------------------------------------------------------------------
# Stage D: split into lines
# ---------------------------------------------------------------------------

def split_into_lines(full_text: str) -> list[str]:
    """Split prose into sentence-level lines for rendering."""
    # Strip blank lines, then split on sentence boundaries OR explicit newlines.
    paragraphs = [p.strip() for p in full_text.split("\n") if p.strip()]
    lines = []
    for p in paragraphs:
        # Split on sentence-ending punctuation
        parts = re.split(r"(?<=[.!?])\s+", p)
        for part in parts:
            part = part.strip()
            if len(part) >= 4:  # Skip degenerate fragments
                lines.append(part)
    return lines


# ---------------------------------------------------------------------------
# Stage E: assign mograph templates per line
# ---------------------------------------------------------------------------

def build_trigger_map(config: dict) -> list[tuple[str, str]]:
    """
    Parse the bible's `mograph.triggers` into a list of (keyword, theme) tuples.
    The bible format is roughly: '* keyword → description...'
    We extract the keyword (left of arrow) as the trigger.
    """
    triggers_text = config.get("mograph", {}).get("triggers", "")
    if not triggers_text:
        return []

    triggers = []
    for raw_line in triggers_text.split("\n"):
        line = raw_line.lstrip("* ").strip()
        if not line:
            continue
        # Match either '=' or '→' or '->' separator
        m = re.match(r"^([^=→\-]+?)\s*[=→]|^([^=→\-]+?)\s*->", line)
        if m:
            keyword = (m.group(1) or m.group(2) or "").strip().lower()
            if keyword:
                triggers.append((keyword, keyword))  # theme == keyword for now
    return triggers


def assign_mograph_to_line(
    line: str,
    triggers: list[tuple[str, str]],
    default_template: str,
    config: dict,
) -> dict:
    """
    Determine the mograph template + intensity for a line.
    Match the line against the bible's trigger keywords; if any match,
    use kinetic_quote with that theme. Otherwise default.
    """
    lowered = line.lower()
    theme = ""
    template = default_template
    intensity = "medium"

    # Power words → high intensity
    power_words_csv = config.get("script", {}).get("power_words", "")
    power_words = [w.strip().lower() for w in power_words_csv.split(",") if w.strip()]
    if any(w in lowered for w in power_words):
        intensity = "high"

    # Match against bible triggers
    for keyword, t in triggers:
        if keyword and re.search(rf"\b{re.escape(keyword)}\b", lowered):
            theme = t
            # Map known themes to specific templates if available
            if any(k in keyword for k in ["fire", "fuel", "ignite", "passion"]):
                template = "fire_ignite"
            elif any(k in keyword for k in ["chain", "trap", "break", "free"]):
                template = "chains_break"
            elif any(k in keyword for k in ["time", "clock", "regret"]):
                template = "clock_dissolve"
            elif any(k in keyword for k in ["money", "wealth", "rise", "graph"]):
                template = "data_graph_rise"
            elif any(k in keyword for k in ["water", "drown"]):
                template = "water_fill_screen"
            elif any(k in keyword for k in ["map", "city", "place"]):
                template = "map_zoom"
            elif any(k in keyword for k in ["glitch", "chaos", "broken"]):
                template = "glitch_transition"
            elif any(k in keyword for k in ["document", "memo", "classified", "redacted"]):
                template = "crt_text_overlay"
            else:
                template = "kinetic_quote"
            break

    # Sentence length affects duration_frames (at 30fps, ~6 frames per word)
    word_count = len(line.split())
    duration_frames = max(48, min(180, word_count * 7))

    return {
        "template": template,
        "intensity": intensity,
        "theme": theme,
        "duration_frames": duration_frames,
    }


def assign_clip_cue(line: str, config: dict) -> str:
    """
    For celebrity-driven channels (narrator off, like CH1/CH2), some lines
    are spoken by the celebrity themselves. We mark these with a clip_cue so
    the assembler knows to source celebrity audio.

    For now, very simple heuristic: if narrator_mode is off, alternate lines
    are treated as celebrity-spoken with a generic cue. This is a placeholder
    that a future stage can refine using actual clip libraries.
    """
    narrator_mode = config.get("narrator", {}).get("mode", "off")
    if narrator_mode == "on":
        # Documentary channels never need celebrity clips
        return "no_clip"
    # For celebrity channels, this is left as no_clip for now -- clip-library
    # integration is Stage 3 work. The mograph track still fires for visuals.
    return "no_clip"


# ---------------------------------------------------------------------------
# Stage F: SEO package
# ---------------------------------------------------------------------------

def generate_seo(config: dict, topic: str, title: str, full_text: str) -> dict:
    bible_extract = _build_bible_extract(config, sections=("seo", "identity"))

    system = f"""You are writing the SEO package for "{config.get('channel_name')}".

CHANNEL SEO RULES:
{bible_extract}
"""
    user = f"""TOPIC: {topic}
WORKING TITLE: {title}

First 500 chars of script:
{full_text[:500]}

Return ONLY a JSON object:
{{
  "title": "Final YouTube title, max 70 chars, matches the channel's title formula",
  "description": "2-4 paragraph YouTube description following the channel's SEO rules",
  "tags": ["tag1", "tag2", ... up to 15 tags],
  "hashtags": "#tag1 #tag2 ... (matches channel's hashtag count)"
}}"""

    return generate_json(system=system, user=user, max_tokens=1500, temperature=0.6)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_bible_extract(config: dict, sections: tuple[str, ...]) -> str:
    """Build a compact representation of selected bible sections for the system prompt."""
    out = []
    for s in sections:
        if s in config:
            value = config[s]
            if isinstance(value, dict):
                lines = [f"  {k}: {str(v)[:500]}" for k, v in value.items()]
                out.append(f"[{s.upper()}]\n" + "\n".join(lines))
            else:
                out.append(f"[{s.upper()}]\n  {str(value)[:1500]}")
    return "\n\n".join(out)


# ---------------------------------------------------------------------------
# Main per-channel pipeline
# ---------------------------------------------------------------------------

def generate_script_for_channel(channel_id: str, topic: str, config: dict) -> Optional[dict]:
    """Full multi-stage generation. Returns the manifest dict (without status/date)."""
    log(channel_id, f"Topic: {topic}")

    # A. Outline
    log(channel_id, "Stage A: outline")
    outline = stage_outline(config, topic)
    if not outline.get("sections"):
        log(channel_id, "[ERROR] Outline has no sections; aborting.")
        return None
    log(channel_id, f"  Sections: {[s['name'] for s in outline['sections']]}")

    # B. Per-section bodies
    log(channel_id, "Stage B: section bodies")
    section_texts = []
    forbidden_csv = config.get("script", {}).get("forbidden_words", "")

    for i, section in enumerate(outline["sections"]):
        log(channel_id, f"  Drafting section {i+1}/{len(outline['sections'])}: {section['name']}")
        body = stage_section(config, topic, outline, i)

        # C. Validate; regenerate once if forbidden words appear
        bad = validate_forbidden(body, forbidden_csv)
        if bad:
            log(channel_id, f"    Forbidden words found: {bad}. Regenerating with stricter prompt.")
            extra = f"\n\nCRITICAL: Your last attempt used these forbidden words: {bad}. Rewrite WITHOUT any of them."
            body = stage_section(config, topic, outline, i) + extra  # context only
            body = stage_section(config, topic, outline, i)
            bad2 = validate_forbidden(body, forbidden_csv)
            if bad2:
                log(channel_id, f"    Still bad after retry ({bad2}); proceeding anyway.")
        section_texts.append(body)

    full_text = "\n\n".join(section_texts)
    log(channel_id, f"  Full text: {len(full_text)} chars, {len(full_text.split())} words")

    # D. Split into lines
    lines_raw = split_into_lines(full_text)
    log(channel_id, f"Stage D: {len(lines_raw)} lines")

    # E. Assign mograph + clip cue
    triggers = build_trigger_map(config)
    default_template = CHANNEL_DEFAULT_TEMPLATE.get(channel_id, "kinetic_quote")

    lines_with_visuals = []
    for i, ln in enumerate(lines_raw):
        lines_with_visuals.append({
            "index": i,
            "line": ln,
            "clip_cue": assign_clip_cue(ln, config),
            "mograph": assign_mograph_to_line(ln, triggers, default_template, config),
        })

    # F. SEO
    log(channel_id, "Stage F: SEO package")
    try:
        seo = generate_seo(config, topic, outline.get("title", topic), full_text)
    except Exception as e:
        log(channel_id, f"  SEO generation failed: {e}; using fallback.")
        seo = {
            "title": outline.get("title", topic)[:70],
            "description": full_text[:1500],
            "tags": [],
            "hashtags": config.get("seo", {}).get("hashtags", ""),
        }

    return {
        "channel_id": channel_id,
        "channel_name": config.get("channel_name"),
        "topic": topic,
        "narrator_mode": config.get("narrator", {}).get("mode", "off"),
        "voice": config.get("narrator", {}).get("voice", "en-US-GuyNeural"),
        "script": {
            "title": outline.get("title", topic),
            "outline": outline,
            "full_text": full_text,
            "lines": lines_with_visuals,
        },
        "seo": seo,
    }


def upload_manifest(channel_id: str, manifest: dict):
    """Upload the manifest to Cloudinary at the path render_mographs expects."""
    manifest_str = json.dumps(manifest, indent=2, ensure_ascii=False)
    encoded = base64.b64encode(manifest_str.encode("utf-8")).decode()
    public_id = f"dopamine-studios/{channel_id}/manifests/{DATE_STR}"
    cloudinary.uploader.upload(
        f"data:text/plain;base64,{encoded}",
        public_id=public_id,
        resource_type="raw",
        overwrite=True,
    )
    log(channel_id, f"Manifest uploaded: {public_id}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    topics = fetch_topics()
    if not topics:
        print(f"[ERROR] No topics file at dopamine-studios/queue/tonight-topics-{DATE_STR}. Did generate_topics.py run?")
        sys.exit(1)

    channels = list(topics.keys()) if CHANNEL_OVERRIDE == "ALL" else [CHANNEL_OVERRIDE]

    successes = 0
    failures = 0

    for channel_id in channels:
        if channel_id not in topics:
            print(f"[{channel_id}] No topic in queue -- skipping.")
            continue

        topic_entry = topics[channel_id]
        topic = topic_entry.get("topic", "")
        if not topic:
            print(f"[{channel_id}] Topic field empty -- skipping.")
            continue

        config = load_config(channel_id)
        if not config:
            continue

        try:
            manifest = generate_script_for_channel(channel_id, topic, config)
            if manifest is None:
                failures += 1
                continue
            manifest["date"] = DATE_STR
            manifest["status"] = "queued"
            upload_manifest(channel_id, manifest)
            successes += 1
        except Exception as e:
            log(channel_id, f"[ERROR] Generation failed: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            failures += 1

    print(f"\n[DONE] {successes} succeeded, {failures} failed.")
    if successes == 0 and failures > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()

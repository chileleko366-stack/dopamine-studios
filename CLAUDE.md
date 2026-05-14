# CLAUDE.md — Dopamine Studios project notes

This file gives any future AI assistant (Claude Code, etc.) the context it needs to make safe, correct changes to this repo. Read this first before editing anything.

## What this project is

A fully automated YouTube content pipeline for 5 channels. Runs entirely in GitHub Actions (no render PC). Generates topics, writes scripts, renders motion graphics with Remotion, assembles videos with ffmpeg, and uploads to YouTube.

## Architecture in 60 seconds

```
10PM SAST (nightly-pipeline.yml)
├── generate_topics.py        Claude API picks tonight's topic per channel
├── write_render_jobs.py      Claude API writes full script + per-line mograph cues
│                              → uploads MANIFEST to Cloudinary
└── render_mographs.py        Remotion renders each line's mograph clip
                              → uploads RENDERED CLIPS to Cloudinary

6AM SAST (main.yml)
├── render_mographs.py        Catch-up renderer (idempotent; skips already done)
├── check_renders.py          Sets has_renders=true/false output
├── generate_voiceover.py     edge-tts for CH3/CH4/CH5 (narrator-on channels)
├── assemble_video.py         ffmpeg concat + voiceover + music
├── generate_thumbnail.py     Claude API picks composition; PIL renders
├── upload_youtube.py         YouTube Data API v3 upload as PRIVATE
├── upload_to_drive.py        Backup copy to Google Drive
└── cleanup_cloudinary.py     Removes today's temp assets
```

## File contracts

### `configs/channel-config-{ch1..ch5}.json`
The "bible" for each channel. ~40-65KB each. Defines: identity, script tone, forbidden words, mograph triggers, sound design, editing pace, shorts formula, thumbnail rules, SEO rules, schedule.

When writing AI prompts in `write_render_jobs.py`, always include the bible as system context. Different sections of the bible feed different stages of generation.

### Cloudinary manifest at `dopamine-studios/{CHANNEL}/manifests/{date}`
Produced by `write_render_jobs.py`. Consumed by `render_mographs.py` and `assemble_video.py`. Shape:
```json
{
  "channel_id": "CH1",
  "channel_name": "DOPAMINE LOOP",
  "date": "2026-05-13",
  "status": "queued" | "rendering" | "rendered" | "assembled",
  "topic": "...",
  "narrator_mode": "off" | "on",
  "voice": "en-US-GuyNeural",
  "script": {
    "title": "...",
    "full_text": "...",
    "lines": [
      {
        "index": 0,
        "line": "spoken sentence here",
        "clip_cue": "kanye_breakdown_2019" | "no_clip",
        "mograph": {
          "template": "kinetic_quote",
          "intensity": "low" | "medium" | "high",
          "theme": "loneliness",
          "duration_frames": 72
        }
      }
    ]
  },
  "seo": { "title": "...", "description": "...", "tags": [...] }
}
```
**Never break this contract.** Downstream scripts assume it.

### Cloudinary rendered clips at `dopamine-studios/{CHANNEL}/rendered/{date}/line{NNN}`
One MP4 per line. `assemble_video.py` concatenates these in order.

### Cloudinary topics file at `dopamine-studios/queue/tonight-topics-{date}`
Produced by `generate_topics.py`. Consumed by `write_render_jobs.py`. Dict keyed by channel_id.

## AI provider policy

**Claude (Anthropic) is primary** for all generation. Gemini is a fallback ONLY for errors after 3 retries. All AI calls go through `scripts/claude_client.py`. **Do not import `google.generativeai` directly anywhere except `claude_client.py`.**

Channel bibles are tuned for Claude's style. Don't add per-call provider switching — that would break the editorial voice.

## Coding conventions

- **Python:** Python 3.11. No type stubs on every line; use them where they clarify, skip on obvious dict-shuffling.
- **Logging:** `print(..., flush=True)` with `[CHANNEL_ID][stage]` prefix. GitHub Actions truncates non-flushed output.
- **Env vars:** Read at module top from `os.environ[...]`. Missing required env should crash early, not silently default.
- **Cloudinary IDs:** `dopamine-studios/{scope}/...`. Never use slashes elsewhere — Cloudinary treats them as folders.
- **Idempotency:** Every script should be safely re-runnable. Use `overwrite=True` on uploads, check existence on writes.

## Remotion conventions

- Compositions are in `remotion/compositions/`. `AllComponents.tsx` is a barrel for 11 compositions; `KineticQuote.tsx` and `ParticlesAscending.tsx` are standalone.
- `Root.tsx` registers all compositions. Add a new composition by exporting it from AllComponents (or as standalone) and registering in Root.
- Compositions take theme props (`primaryColor`, `backgroundColor`, `intensity`) so the same composition serves all 5 channels.
- 30fps. Long-form is 1920x1080. Shorts are 1080x1920 (handled by props/CSS, same compositions).

## Channel-specific notes

- **CH1 DOPAMINE LOOP** — narrator_mode=off (celebrity audio drives), TUE/FRI
- **CH2 FINANCEFICTION** — narrator_mode=off (celebrity audio drives), MON/THU? (check config)
- **CH3 REDACTED** — narrator_mode=on, `en-US-GuyNeural`, MON/THU
- **CH4 THE GREY MATTER** — narrator_mode=on, `en-GB-LibbyNeural`, TUE/FRI
- **CH5 THE QUIET RECORD** — narrator_mode=on, `en-GB-RyanNeural`, WED/SAT

CH3/CH4/CH5 always need `generate_voiceover.py` to run before `assemble_video.py`. CH1/CH2 do not.

## Secrets needed in GitHub repo settings

Required for the pipeline to function:
- `ANTHROPIC_API_KEY` — Claude (required)
- `GEMINI_API_KEY` — fallback (optional but recommended)
- `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`
- `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`
- `YOUTUBE_REFRESH_TOKEN_CH1` through `_CH5` — one per channel

To generate the YouTube refresh tokens, run `scripts/get_youtube_token.py` locally (or in a Codespace) for each channel.

## Known sharp edges

- **YouTube upload quota:** ~6 uploads/day per Google Cloud project. If running 5 channels daily, use 5 separate projects (one per channel) or batch on alternate days.
- **Cloudinary free tier:** 25GB storage, 25GB bandwidth/month. Cleanup script must run nightly to stay under.
- **Edge-TTS rate limits:** No hard limit but bursts can fail. Generate sequentially per channel.
- **Remotion render in Actions:** ~2-4 min per 60s 1080p clip on free runner. Long videos with many mograph lines = many minutes. Budget the cron accordingly.

## Things NOT to do

- Don't add Gemini calls outside `claude_client.py`
- Don't import from `AllComponents.tsx` individual file paths like `./AllComponents/DataGraphRise` — it's a single module
- Don't change the manifest contract without updating both producer (`write_render_jobs.py`) and consumers (`render_mographs.py`, `assemble_video.py`)
- Don't add Blender references (the render PC was abandoned May 2026)
- Don't commit secrets, ever

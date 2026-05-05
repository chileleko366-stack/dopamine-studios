# DopamineStudios — Operations Guide
## GitHub Actions + Cloudinary Pipeline

---

## WHAT'S BEEN BUILT

### GitHub Actions Workflows (3 files)
| File | Triggers | Does |
|---|---|---|
| `nightly-pipeline.yml` | 10PM SAST (20:00 UTC) | Generates topics, notifies Telegram |
| `render-trigger.yml` | 11PM SAST (21:00 UTC) | Writes render jobs to Cloudinary |
| `morning-assembly.yml` | 6AM SAST (04:00 UTC) | Assembles + uploads all channels |

### Python Scripts (9 files)
| Script | When it runs | Does |
|---|---|---|
| `generate_topics.py` | 10PM in GitHub Actions | Reads channel configs, calls Claude, generates tonight's topic per channel |
| `write_render_jobs.py` | 11PM in GitHub Actions | Full script generation + mograph tags, drops job JSONs to Cloudinary |
| `telegram_notify.py` | 10PM, 11PM, 6AM | Sends topic preview, render alert, morning summary to your phone |
| `watcher.py` | 24/7 on render PC | Polls Cloudinary, fires Blender headlessly, uploads clips back |
| `check_renders.py` | 6AM in GitHub Actions | Checks if render PC finished before assembly starts |
| `assemble_video.py` | 6AM in GitHub Actions | Downloads clips, ffmpeg assembly, adds music/voiceover |
| `generate_voiceover.py` | 6AM — CH3 + CH5 only | Edge TTS narration for documentary channels |
| `generate_thumbnail.py` | 6AM in GitHub Actions | Cloudinary template or Pillow fallback thumbnail |
| `upload_youtube.py` | 6AM in GitHub Actions | YouTube Data API v3 upload with full SEO metadata |
| `cleanup_cloudinary.py` | 6AM after upload | Deletes all temp assets, keeps thumbnails + SEO |

### Channel Configs (5 files in `configs/`)
- `channel-config-ch1.json` — DopamineLoop ✅ (your full config loaded)
- `channel-config-ch2.json` — Finance ✅ (your full config loaded)
- `channel-config-ch3.json` — Conspiracy (placeholder — fill in)
- `channel-config-ch4.json` — Psychology (placeholder — fill in)
- `channel-config-ch5.json` — History (placeholder — fill in)

---

## ONE-TIME SETUP (do this once, never again)

### STEP 1 — Create GitHub repo
```
1. Go to github.com → New repository
2. Name: dopamine-studios
3. Private repo ✓
4. Upload ALL these files maintaining the folder structure
```

### STEP 2 — Add GitHub Actions Secrets
Go to: `github.com/YOUR_USERNAME/dopamine-studios → Settings → Secrets → Actions`

Add these secrets exactly:

```
ANTHROPIC_API_KEY          your Claude API key from console.anthropic.com
CLOUDINARY_CLOUD_NAME      from cloudinary.com → Dashboard
CLOUDINARY_API_KEY         from cloudinary.com → Dashboard
CLOUDINARY_API_SECRET      from cloudinary.com → Dashboard
TELEGRAM_BOT_TOKEN         from @BotFather on Telegram
TELEGRAM_CHAT_ID           your personal chat ID (see Step 3)
YOUTUBE_CLIENT_ID          from Google Cloud Console (see Step 4)
YOUTUBE_CLIENT_SECRET      from Google Cloud Console (see Step 4)
YOUTUBE_REFRESH_TOKEN_CH1  from get_youtube_token.py (see Step 4)
YOUTUBE_REFRESH_TOKEN_CH2  run get_youtube_token.py logged into CH2's account
YOUTUBE_REFRESH_TOKEN_CH3  etc.
YOUTUBE_REFRESH_TOKEN_CH4  etc.
YOUTUBE_REFRESH_TOKEN_CH5  etc.
```

### STEP 3 — Create Telegram Bot (5 minutes)
```
1. Open Telegram → search @BotFather → /newbot
2. Name it: DopamineStudios Bot
3. Username: dopaminestudios_bot (or similar)
4. BotFather gives you the BOT_TOKEN → save it
5. Message your new bot once (say anything)
6. Visit: https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
7. Find "chat":{"id": 123456789} → that number is your CHAT_ID
```

### STEP 4 — YouTube OAuth (run once per channel)
```
1. Google Cloud Console → dopamine-loop project (already exists)
2. APIs & Services → Credentials → + Create Credentials → OAuth 2.0 Client ID
3. Application type: Desktop App → Create
4. Download JSON → save as client_secret.json in project root
5. On your LOCAL PC (not GitHub):
   pip install google-auth-oauthlib
   python scripts/get_youtube_token.py
6. Browser opens → sign in with CH1's YouTube Google account
7. Copy the printed refresh token → GitHub secret YOUTUBE_REFRESH_TOKEN_CH1
8. Repeat steps 5-7 for each channel (log in with that channel's account each time)
```

### STEP 5 — Set up render PC watcher
```
1. Open watcher.py in Notepad on the render PC
2. Fill in the 3 config lines at the top:
   CLOUDINARY_CLOUD_NAME = "your_cloud_name"
   CLOUDINARY_API_KEY    = "your_api_key"
   CLOUDINARY_API_SECRET = "your_api_secret"
3. Install dependencies (once):
   pip install cloudinary requests
4. Test it runs:
   python watcher.py
5. Set it to run on startup:
   Win+R → shell:startup → create shortcut to: python C:\path\to\watcher.py
6. Disable sleep/hibernate:
   Control Panel → Power Options → Never sleep, never hibernate
```

### STEP 6 — Create Cloudinary folder structure
In Cloudinary Media Library, create these folders:
```
dopamine-studios/
dopamine-studios/queue/
dopamine-studios/CH1/assets/
dopamine-studios/CH1/rendered/
dopamine-studios/CH1/thumbnails/
dopamine-studios/CH1/manifests/
dopamine-studios/CH1/published/
dopamine-studios/CH2/   (same subfolders)
dopamine-studios/CH3/
dopamine-studios/CH4/
dopamine-studios/CH5/
dopamine-studios/BlenderTemplates/  ← upload your .blend files here
```

### STEP 7 — Upload your Blender templates to Cloudinary
```
Upload all .blend files to: dopamine-studios/BlenderTemplates/
Name them exactly:
  prison_bars_closing.blend
  shrinking_room.blend
  water_fill_screen.blend
  particles_ascending.blend
  maze_fragment.blend
  clock_dissolve.blend
  fire_ignite.blend
  chains_break.blend
  data_graph_rise.blend
  map_zoom.blend
  kinetic_quote.blend  ← most important, used as fallback
```

---

## HOW IT RUNS EVERY NIGHT (fully automatic after setup)

```
10:00 PM  GitHub Actions fires → generate_topics.py runs
          Claude reads your channel configs
          Generates one topic per channel scheduled tonight
          Telegram message arrives on your phone showing all topics

10:00 PM  You have 60 minutes to override anything
          Reply format: OVERRIDE CH1 Your new topic here
          Or do nothing — auto topics are used

11:00 PM  GitHub Actions fires → write_render_jobs.py runs
          Claude generates full scripts with mograph tags
          Render job JSONs uploaded to Cloudinary queue
          Telegram: "Render jobs queued — PC should be picking up"

11:00 PM  watcher.py on render PC detects new job files
          Blender fires headlessly for each mograph clip
          Rendered clips uploaded to Cloudinary
          Render manifest written back to Cloudinary

Overnight  Blender works through all channels sequentially

 6:00 AM  GitHub Actions fires → morning-assembly.yml runs
          Per channel (parallel):
            ✓ check_renders.py — confirms PC finished
            ✓ generate_voiceover.py — Edge TTS for CH3/CH5
            ✓ assemble_video.py — downloads clips, ffmpeg assembly
            ✓ generate_thumbnail.py — creates thumbnail
            ✓ upload_youtube.py — uploads with full SEO, scheduled publish
            ✓ cleanup_cloudinary.py — deletes temp files
          Telegram: morning summary of what uploaded
```

---

## YOUR DAILY JOB (30 seconds)

```
1. Before 11PM — make sure the render PC is on
2. Check Telegram at 10PM — approve or override topics
3. Check Telegram at 6AM — confirm uploads succeeded
```

That's it. Everything else is automatic.

---

## MANUAL OVERRIDES (from phone)

**Run pipeline for one channel only:**
GitHub → Actions → Nightly Video Pipeline → Run workflow
→ channel_id: CH1 (or CH2, etc.)

**Force a specific topic:**
GitHub → Actions → Nightly Video Pipeline → Run workflow
→ channel_id: CH1
→ override_topic: Your topic here

**Re-run morning assembly if something failed:**
GitHub → Actions → 6AM Morning Assembly → Run workflow

---

## TROUBLESHOOTING

| Problem | Fix |
|---|---|
| Telegram not sending | Check BOT_TOKEN and CHAT_ID secrets. Message your bot once manually first. |
| Render PC not picking up jobs | Make sure watcher.py is running. Check Cloudinary credentials in watcher.py. |
| Blender crashes | Check BLENDER_PATH in watcher.py is correct. Confirm .blend file exists. |
| YouTube upload fails | Re-run get_youtube_token.py for that channel — refresh tokens expire if unused. |
| "No manifest" at 6AM | Render PC didn't finish. Re-run morning assembly the next day manually. |
| Cloudinary out of storage | cleanup_cloudinary.py may have missed a run. Delete rendered/ folders manually. |

---

## COSTS — CONFIRMED $0/MONTH

| Service | Cost | Limit |
|---|---|---|
| GitHub Actions | $0 | 2,000 min/month free (you'll use ~200) |
| Cloudinary | $0 | 25GB storage, 25GB bandwidth free |
| Anthropic API | $0 | Free tier (watch usage — upgrade if needed) |
| Edge TTS | $0 | Unlimited |
| YouTube Data API | $0 | Unlimited uploads |
| Telegram Bot API | $0 | Unlimited |
| Render PC | $0 | Your existing hardware |

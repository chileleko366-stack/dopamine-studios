# SKILL: Sound Design & B-Roll Audio
## Injected into assemble_video.py and write_render_jobs.py

---

## WHY THIS MATTERS
Bad sound design is the #1 thing that makes content feel cheap and AI-generated.
Most automated channels have zero sound design — just music + voice.
Adding targeted SFX is what separates $0 content from content that feels produced.

---

## THE SOUND LAYER SYSTEM — 4 layers, always

```
LAYER 1: VOICE     — Celebrity/narrator — volume 1.0 — always on top
LAYER 2: MUSIC     — Background score — volume 0.06-0.10 — ducks under voice
LAYER 3: AMBIENCE  — Room tone / environment — volume 0.04 — constant, subtle
LAYER 4: SFX       — Punctuation hits, whooshes, transitions — volume 0.3-0.6
```

If you only have layers 1 and 2, it sounds like a slideshow.
Layers 3 and 4 are what makes it feel like a real production.

---

## SFX TRIGGER MAP — Claude assigns these in the script

Add to write_render_jobs.py prompt:
```
For each script line, also assign an SFX_CUE tag from this list:
[SFX_NONE]       = no sound effect
[SFX_HIT]        = deep bass hit — use on shocking facts, reversals
[SFX_WHOOSH]     = transition whoosh — use on mograph cuts
[SFX_GLITCH]     = digital glitch burst — CH1/CH3 only, on dramatic cuts
[SFX_TYPEWRITER] = typewriter keys — CH3/CH5 documentary, on text reveals
[SFX_HEARTBEAT]  = low thumping pulse — tension building moments
[SFX_VINYL]      = vinyl record crackle — CH1 VHS aesthetic, under quiet moments
[SFX_STINGER]    = sharp musical sting — on shocking statistics
[SFX_BREATH]     = subtle inhale — just before a big reveal
[SFX_STATIC]     = TV static burst — CH1/CH3, on scene transitions
```

### Usage rules
```
- Maximum 1 SFX every 4 seconds — restraint creates impact
- SFX_HIT: only 2-3 times per video — overuse kills it
- SFX_WHOOSH: every mograph cut — this one is constant
- Never layer two SFX simultaneously
- SFX volume must never exceed 60% of voice volume
```

---

## FREE SFX SOURCES — Automated download in pipeline

### Freesound.org API (free, no attribution for most)
```python
# In assemble_video.py — download SFX library once, cache in Cloudinary

FREESOUND_SFX_IDS = {
    "SFX_HIT":        "522382",   # Deep bass thud
    "SFX_WHOOSH":     "519413",   # Fast whoosh
    "SFX_GLITCH":     "476178",   # Digital glitch
    "SFX_TYPEWRITER": "109401",   # Typewriter keys
    "SFX_HEARTBEAT":  "189583",   # Heartbeat
    "SFX_VINYL":      "137065",   # Vinyl crackle
    "SFX_STINGER":    "435934",   # Sharp sting
    "SFX_BREATH":     "400026",   # Breath inhale
    "SFX_STATIC":     "243022",   # TV static
}

# Download via Freesound API (free account, API key required)
# Store in: dopamine-studios/assets/sfx/ on Cloudinary
```

### Alternative — ZapSplat (free with account)
```
zapslat.com → create free account → download as MP3
Categories to download:
  Transitions → whooshes, swipes
  Impacts → hits, thuds, thumps  
  Technology → glitches, static, digital
  Human → breathing, heartbeat
  Vintage → vinyl, tape, VHS
Upload all to: Cloudinary → dopamine-studios/CH1/assets/sfx/
```

---

## AMBIENCE LAYER — Per Channel

```
CH1 DopamineLoop:  Low city ambience + subtle VHS tape hiss
                   Creates intimacy, like watching something recorded late at night

CH2 Finance:       Clean office ambience — air conditioning hum
                   Feels like a Bloomberg studio

CH3 Conspiracy:    Subtle room tone — almost silence with faint electrical hum
                   Makes viewer lean in. Uncomfortable silence = tension.

CH4 Psychology:    Soft rain or library ambience
                   Academic, thoughtful, considered

CH5 History:       Wind or distant crowd — era-appropriate atmosphere
                   If discussing 1940s: subtle period ambience
```

### Ambience sources (all free)
```
freemusicarchive.org → ambient section
archive.org → sound effects library
YouTube Audio Library → ambient/atmosphere filter
```

---

## MUSIC SELECTION RULES — Per Channel

### What to avoid (AI playlist sound)
```
- Lo-fi hip hop beats (every AI channel uses this)
- Tropical house (used for finance content — completely overdone)
- Dramatic orchestral swells at predictable intervals
- Any track that sounds like it's from Epidemic Sound's top 20
```

### What to use instead

```
CH1 DopamineLoop:
  Dark trap with 808s — not upbeat, not happy, brooding
  Think: Travis Scott instrumentals feel, not corporate motivation
  BPM: 70-90 — slow and heavy

CH2 Finance:
  Minimal techno or dark ambient — clinical and cold
  Sounds like: The Social Network OST (Trent Reznor feel)
  BPM: irrelevant — atmospheric, not rhythmic

CH3 Conspiracy:
  Drone music + subtle dissonance
  Never use music that resolves — always leave it unresolved
  Think: true crime podcast music

CH4 Psychology:
  Cinematic piano + strings — sparse, not lush
  Single piano note with long reverb > full orchestra
  BPM: 60-75

CH5 History:
  Orchestral but minimal — not Hollywood epic, more PBS documentary
  Sparse strings + room tone
  Era-appropriate instrumentation where possible
```

### Free music sources with correct sound
```
Free Music Archive → search "dark ambient", "drone", "minimal"
ccMixter.org → search by mood
Incompetech.com (Kevin MacLeod) → filter by mood: Dark, Mysterious
Archive.org → netlabel collection
```

---

## AUDIO MIX SETTINGS — In assemble_video.py ffmpeg

```python
# Complete audio mix filter for all channels
AUDIO_MIX_FILTER = (
    # Voice: full volume, slight compression
    "[0:a]volume=1.0,acompressor=threshold=0.5:ratio=4:attack=5:release=50[voice];"
    
    # Music: low volume, ducking under voice
    "[1:a]volume=0.07,aloop=loop=-1:size=2e+09[music_loop];"
    
    # Ambience: very low, constant
    "[2:a]volume=0.04,aloop=loop=-1:size=2e+09[amb_loop];"
    
    # SFX: punchy, no compression
    "[3:a]volume=0.45[sfx];"
    
    # Mix everything
    "[voice][music_loop][amb_loop][sfx]amix=inputs=4:duration=first:dropout_transition=0[final_mix]"
)

# If no ambience or SFX track exists for that video, fall back to:
AUDIO_MIX_SIMPLE = (
    "[0:a]volume=1.0[voice];"
    "[1:a]volume=0.07,aloop=loop=-1:size=2e+09[music];"
    "[voice][music]amix=inputs=2:duration=first[out]"
)
```

---

## SFX PLACEMENT — In assemble_video.py

```python
# For each clip in the manifest that has an SFX_CUE tag:
# Calculate the timestamp and overlay the SFX at that exact point

def build_sfx_timeline(clips_manifest: list, sfx_library: dict) -> list:
    """
    Returns list of: {timestamp_seconds, sfx_file, volume}
    For use in ffmpeg adelay filter
    """
    sfx_events = []
    current_time = 0.0

    for clip in clips_manifest:
        sfx_cue = clip.get("sfx_cue", "SFX_NONE")
        clip_duration = clip.get("duration_seconds", 3.0)

        if sfx_cue != "SFX_NONE" and sfx_cue in sfx_library:
            sfx_events.append({
                "timestamp_ms": int(current_time * 1000),
                "sfx_file": sfx_library[sfx_cue],
                "volume": 0.45,
            })

        current_time += clip_duration

    return sfx_events
```

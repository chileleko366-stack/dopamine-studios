# SKILL: High-End Cut & Mograph Direction
## Injected into write_render_jobs.py mograph decision logic

---

## THE CARDINAL RULE
Every cut must be MOTIVATED. A cut exists because something changed —
emotion, energy, information, or rhythm. Never cut just to fill time.

---

## CUT RHYTHM — The Pattern That Separates Pro From Amateur

### For Motivational / Celebrity Channels (CH1, CH2, CH4)
```
Fast-fast-fast → HOLD (let face breathe 2-3 sec)
Fast-fast → MOGRAPH (3 sec)
Hold on face during emotional peak — NEVER cut away at the money moment
Cut to B-roll during setup, return to face for the punchline
```

### For Documentary Channels (CH3, CH5)
```
Image/clip → hold longer than feels comfortable (4-5 sec)
Evidence clip → narrator bridge → next evidence
Never cut mid-sentence unless for extreme dramatic effect
Silence + static image = more powerful than constant cutting
```

---

## MOGRAPH TRIGGER RULES — Quality over quantity

### When to use mograph (the right reasons)
- Emotional punctuation: the script says something heavy — HOLD on abstract visual
- Data/stats moment: numbers need visualization
- Transition between story chapters
- Opening hook — first 5 seconds must be visually arresting

### When NOT to use mograph (common AI mistakes)
- Don't cut to mograph just because no clip exists — hold on face instead
- Don't use particle effects for calm/contemplative moments
- Don't use kinetic text for every line — it loses impact
- Don't use clock_dissolve unless time is literally being discussed

---

## MOGRAPH QUALITY RULES — Blender template direction

### Speed mapping — intensity must match emotion
```python
INTENSITY_TO_SPEED = {
    "contemplative": 0.2,   # Barely moving. Heavy.
    "building":      0.5,   # Slow escalation
    "medium":        0.6,   # Default
    "urgent":        0.8,   # Things are moving fast
    "explosive":     1.0,   # Maximum energy
}
```

### Color rules — inject into Blender Python
- Match channel palette EXACTLY — not approximate
- CH1 DopamineLoop: primary #0a0a0a, accent #e8ff47 (electric yellow)
- CH2 Finance: primary #0d1117, accent #00d4aa (clean teal)
- CH3 Conspiracy: primary #0d0d0d, accent #ff3333 (blood red)
- CH4 Psychology: primary #0a0a1a, accent #7b61ff (deep purple)
- CH5 History: primary #1a1008, accent #c8a24b (aged gold)

### The 3-second rule
Every mograph clip is 3 seconds. Not 2. Not 4. 3.
At 24fps = 72 frames. Non-negotiable.
Exception: intro sequences (5-8 sec) and end screens (5-10 sec)

---

## CUT PACING — Claude tags in script generation

Add to script generation prompt:
```
For every script line, assign a CUT_SPEED tag:
[CUT_HOLD]   = stay on current visual for 3+ seconds — emotional weight
[CUT_FAST]   = cut within 1 second — rapid fire energy  
[CUT_NORMAL] = standard 2-3 second hold
[CUT_BREATH] = 0.5 second black frame before next clip — dramatic pause
```

---

## ASSEMBLY RULES — In assemble_video.py

### Transition types — use in ffmpeg
```python
TRANSITIONS = {
    "hard_cut":     "",                          # No transition — most used
    "glitch":       "xfade=transition=pixelize", # CH1 VHS style
    "fade_black":   "xfade=transition=fade",     # Documentary chapters
    "whip":         "xfade=transition=slideleft", # High energy moments
}

# Rule: 80% hard cuts, 15% glitch/whip, 5% fade
# Never use dissolve — it looks like PowerPoint
```

### Audio cut rules — inject into assembly
```python
# Music ducks during speech (sidechain effect)
# ffmpeg filter for ducking:
MUSIC_DUCK_FILTER = (
    "[0:a]volume=1.0[speech];"
    "[1:a]volume=0.08[music];"
    "[speech][music]amix=inputs=2:duration=first[out]"
)

# Hard cut audio with the video — no audio crossfade
# Exception: documentary chapter breaks — 0.3s audio fade
```

---

## THUMBNAIL RULES — generate_thumbnail.py direction

### What makes a thumbnail stop the scroll
1. Human face with extreme expression OR no face at all — never neutral face
2. Maximum 4 words of text — 3 is better — 2 is best
3. High contrast: dark bg + bright text OR bright bg + dark text
4. One focal point. Not two. One.
5. The text completes what the face/image implies — they work together

### Forbidden thumbnail choices
- Stock photo hands / generic business imagery
- Text that says exactly what the title says (redundant)
- More than 2 colors in the design
- Centered text with no visual anchor
- Any font that isn't bold weight

### Text rules for thumbnails
```python
THUMBNAIL_TEXT_MAX_WORDS = 4
THUMBNAIL_FONT_WEIGHT = "Black"  # Heaviest weight available
THUMBNAIL_TEXT_CASE = "UPPER"    # Always uppercase
```

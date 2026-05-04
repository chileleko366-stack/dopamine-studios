# SKILL: On-Screen Typography & Text Direction
## Injected into generate_thumbnail.py, assemble_video.py, and Blender template direction

---

## THE AI FONT PROBLEM
Every AI-generated video uses the same 3 fonts:
- Montserrat Bold (overused to death)
- Bebas Neue (every gym/motivation channel)
- Impact (meme font — instant credibility killer)

These fonts signal AI immediately to any viewer who's seen more than 10 YouTube videos.

---

## FONT SYSTEM — Per Channel

### CH1 — DopamineLoop (VHS/Motivation)
```
PRIMARY FONT:    Neue Haas Grotesk Display Pro Black
                 Free alternative: "Anton" (Google Fonts)
SECONDARY FONT:  PP Neue Machina (geometric, techy)
                 Free alternative: "Space Grotesk Bold" (Google Fonts)
ACCENT FONT:     VCR OSD Mono (for VHS/CRT text overlays ONLY)
                 Free alternative: "Share Tech Mono" (Google Fonts)
NEVER USE:       Montserrat, Bebas Neue, Impact, Oswald
```

### CH2 — Finance (Clean/Sharp)
```
PRIMARY FONT:    Söhne (Klim Type Foundry)
                 Free alternative: "Inter Black" (Google Fonts)
SECONDARY FONT:  Druk Wide Bold
                 Free alternative: "Barlow Condensed ExtraBold" (Google Fonts)
DATA FONT:       IBM Plex Mono (numbers, stats, data)
NEVER USE:       Montserrat, Lato, Roboto (too generic)
```

### CH3 — Conspiracy (Dark/Investigative)
```
PRIMARY FONT:    Suisse Int'l Condensed Bold
                 Free alternative: "Barlow Condensed Black" (Google Fonts)
SECONDARY FONT:  Courier Prime (typewriter feel for "leaked documents")
                 Free: "Courier Prime" (Google Fonts)
ACCENT FONT:     Redacted Script (for redacted text effect)
                 Free: "Redacted" (Google Fonts)
NEVER USE:       Any sans-serif that looks clean/corporate
```

### CH4 — Psychology (Cinematic/Academic)
```
PRIMARY FONT:    Canela Text Bold
                 Free alternative: "DM Serif Display" (Google Fonts)
SECONDARY FONT:  Graphik Medium
                 Free alternative: "Outfit Medium" (Google Fonts)
NEVER USE:       Anything that looks like a PowerPoint
```

### CH5 — History (Documentary/Archive)
```
PRIMARY FONT:    Tiempos Headline Bold
                 Free alternative: "Playfair Display Black" (Google Fonts)
SECONDARY FONT:  Freight Text Pro
                 Free alternative: "Libre Baskerville Bold" (Google Fonts)
ACCENT FONT:     Typewriter-style for "archive documents"
                 Free: "Special Elite" (Google Fonts)
NEVER USE:       Any modern sans-serif — kills the era feeling
```

---

## TEXT ANIMATION RULES — What separates pro from amateur

### The 3 Timing Rules
```
1. Text appears WITH the word being spoken — not before, not after
   Sync to audio within 2 frames (0.08 seconds at 24fps)

2. Text stays on screen for minimum 1.5 seconds — never flash and disappear
   Exception: rapid-fire lists — 0.5 seconds per item is intentional

3. Text EXIT animation = half the speed of entrance
   Fast in, slow out = professional
   Fast in, fast out = amateur
```

### Entrance Animations — Use these
```
SLAM:       Scale from 120% to 100% in 4 frames — aggressive, impactful
SLIDE_UP:   Y position +40px to 0 in 8 frames — smooth, confident  
FADE_MASK:  Text reveals left to right via mask — editorial, premium
TYPEWRITER: Character by character — documentary/conspiracy channels only
NONE:       Hard cut appearance — used for single bold words mid-sentence
```

### Exit Animations — Use these
```
FADE:       Opacity 100% to 0% over 12 frames — clean
SLIDE_DOWN: Y position 0 to +20px while fading — elegant
HOLD_CUT:   No exit animation — text just cuts with the next clip
```

### NEVER USE
```
- Spinning text
- 3D rotation entrance
- Bounce physics
- Drop shadow + glow together (pick one)
- Rainbow or gradient text (exception: very specific retro aesthetic)
- Text that pulses or breathes continuously
```

---

## ON-SCREEN TEXT CONTENT RULES

### Word count per text element
```
Single emphasis word:  1-2 words — MAXIMUM impact
Key phrase:            3-5 words — standard overlay
Quote fragment:        6-8 words — must be the most important line
Never show:            Full sentences as text overlay — that's a subtitle, not an emphasis
```

### Hierarchy system — 3 levels only
```
LEVEL 1 (Hero text):   Large, centered, full screen moment — used sparingly
LEVEL 2 (Overlay):     Mid-size, bottom third or top third — most common
LEVEL 3 (Accent):      Small, corner placement — stats, timestamps, labels
```

### Contrast rules — text must always be readable
```
Light text on dark: minimum contrast ratio 7:1
Dark text on light: minimum contrast ratio 7:1
Add a subtle text shadow (1px, 30% opacity) if background is busy
NEVER use mid-grey text on mid-grey background
```

---

## BLENDER TEXT OBJECT SETUP — In kinetic_quote.blend and all text templates

```python
# In the Blender Python injection script, set these properties:
# Font loading
text_obj.data.font = bpy.data.fonts.load(r"C:\DopamineStudios\Fonts\Anton-Regular.ttf")

# Character spacing — slightly tighter than default looks more professional
text_obj.data.space_character = 0.95

# Word spacing
text_obj.data.space_word = 1.0

# All caps for emphasis overlays
text_obj.data.body = text_content.upper()

# Extrude very slightly for depth without looking 3D
text_obj.data.extrude = 0.002
```

---

## FONT DOWNLOAD SCRIPT — Add to repo setup

```python
# download_fonts.py — run once on the render PC
# Downloads all Google Fonts needed for all 5 channels
import urllib.request, os

FONTS = {
    "Anton-Regular.ttf": "https://fonts.gstatic.com/s/anton/v25/1Ptgg87LROyAm0K08i4gS7lu.woff2",
    "SpaceGrotesk-Bold.ttf": "https://fonts.gstatic.com/s/spacegrotesk/v16/V8mQoQDjQSkFtoMM3T6r8E7mF71Q-gozwUi9uA.woff2",
    "Inter-Black.ttf": "https://fonts.gstatic.com/s/inter/v13/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuLyfAZ9hiJ-Ek-_EeA.woff2",
    "BarloCondensed-Black.ttf": "https://fonts.gstatic.com/s/barlowcondensed/v12/HTxwL3I-JCGChYJ8VI-L6OO_au7B4xLb.woff2",
    "PlayfairDisplay-Black.ttf": "https://fonts.gstatic.com/s/playfairdisplay/v37/nuFiD-vYSZviVYUb_rj3ij__anPXDTzYgEM86xRbHekyp4tU.woff2",
}

os.makedirs(r"C:\DopamineStudios\Fonts", exist_ok=True)
for filename, url in FONTS.items():
    path = rf"C:\DopamineStudios\Fonts\{filename}"
    if not os.path.exists(path):
        print(f"Downloading {filename}...")
        urllib.request.urlretrieve(url, path)
        print(f"  Saved: {path}")
print("All fonts ready.")
```

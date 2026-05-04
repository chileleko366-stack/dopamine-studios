# SKILL: Thumbnail, Title & SEO System
## Injected into generate_thumbnail.py, upload_youtube.py, write_render_jobs.py

---

## THUMBNAIL SYSTEM

### The 3 thumbnail templates per channel — Claude picks one per video

#### TEMPLATE A — "FACE + WORDS" (celebrity channels CH1 CH2 CH4)
```
Layout:    Celebrity face takes 60% of frame, cropped dramatically
Text:      2-3 words MAX, bottom third, huge, bold
Contrast:  Dark vignette over face edges, text pops clean
When:      Celebrity's expression matches the topic emotion
```

#### TEMPLATE B — "FULL TEXT" (when no good face image available)
```
Layout:    Channel-colored background, giant text centered
Subtext:   1 smaller line below (optional)
Accent:    One geometric shape or line element only
When:      Abstract topics, no strong face available
```

#### TEMPLATE C — "SPLIT REVEAL" (conspiracy/history CH3 CH5)
```
Layout:    Left half: dark archival image. Right half: solid channel color + text
Text:      1 line left side, 1 line right side — completes a sentence across the split
When:      Evidence-based content, documentary style
```

---

### Thumbnail text — Claude generates in write_render_jobs.py

Add to prompt:
```
Generate 3 thumbnail text options for this video.
Format for each:
  LINE1: [max 2 words — the hook]
  LINE2: [max 2 words — the twist or name] (optional)
  TEMPLATE: [A, B, or C]
  EMOTION: [shocked/curious/serious/intrigued]

Rules:
- Never repeat the title word for word
- Must create curiosity gap with the title together
- Numbers beat adjectives: "$47M" beats "MILLIONS"
- Name + emotion beats abstract: "KANYE BROKE" beats "LOSING IT ALL"
```

---

### Thumbnail color rules — hardcoded per channel
```python
THUMBNAIL_PALETTES = {
    "CH1": {"bg": "#0a0a0a", "text": "#e8ff47", "accent": "#ffffff"},
    "CH2": {"bg": "#0d1117", "text": "#ffffff", "accent": "#00d4aa"},
    "CH3": {"bg": "#0d0d0d", "text": "#ff3333", "accent": "#ffffff"},
    "CH4": {"bg": "#0a0a1a", "text": "#ffffff", "accent": "#7b61ff"},
    "CH5": {"bg": "#1a1008", "text": "#c8a24b", "accent": "#ffffff"},
}
```

---

## TITLE SYSTEM

### Title formula per channel type

#### Celebrity/Motivation (CH1 CH4)
```
FORMULA: [Name] + [Did/Said/Lost/Built] + [Specific thing]
EXAMPLES:
  "Kanye Lost $50M and Didn't Blink"
  "How Elon Built SpaceX While Broke"
  "The Night Kobe Decided Everything"

NOT:
  "Kanye West's Incredible Journey to Success"
  "Top 5 Lessons from Elon Musk"
```

#### Finance (CH2)
```
FORMULA: [Specific number/fact] + [Contradiction or result]
EXAMPLES:
  "He Made $200M Then Filed for Bankruptcy"
  "The $1 Stock That Became $10,000"
  "Why Rich People Keep No Cash"

NOT:
  "How to Build Wealth Like the Ultra Rich"
```

#### Conspiracy (CH3)
```
FORMULA: [Official story] + [vs] + [What really happened]
OR:      [Year] + [Event] + [Hidden detail]
EXAMPLES:
  "The Moon Landing Detail NASA Never Explained"
  "1963. Dallas. The Third Man Nobody Saw."
  "Why This File Is Still Classified in 2025"

NOT:
  "Shocking Conspiracy Theory You Won't Believe"
```

#### History (CH5)
```
FORMULA: [Specific moment] + [Consequence nobody talks about]
EXAMPLES:
  "The Decision That Ended the Roman Empire Overnight"
  "One Telegram. The Start of World War I."
  "He Surrendered. The War Should Have Ended. It Didn't."

NOT:
  "The Fascinating History of Ancient Rome"
```

---

### Title scoring — Claude scores before finalising (regenerate if below 7)
```
Contains specific name or number:     +3
Creates curiosity without lying:      +2
Under 10 words:                       +2
Has tension or contradiction:         +2
Would YOU click this:                 +1
Score below 7: regenerate the title
```

---

## SEO SYSTEM

### Tags strategy — 13 tags total, never repeat title words
```python
def build_tags(topic, celebrity, channel_niche):
    return [
        # 5 ultra-specific (exact moment/person/event)
        f"{celebrity} {topic_keyword}",
        f"{celebrity} story",
        f"{topic_keyword} explained",
        f"{topic_keyword} {year}",
        f"what happened to {celebrity}",
        
        # 5 medium (related niche)
        f"{channel_niche} stories",
        f"motivational stories",
        f"{celebrity} biography",
        f"success failure story",
        f"untold story",
        
        # 3 broad (general)
        "documentary",
        "biography",
        channel_niche,
    ]
```

### Description template — per channel
```
CH1/CH4 MOTIVATION:
  Line 1-2: Most shocking fact from the video (hook)
  Line 3:   "In this video:" + one sentence summary
  Line 4:   Timestamp if long-form: 0:00 Intro / 2:30 The turning point
  Line 5:   Question to drive comments: "What would you have done?"
  Line 6-7: 5 hashtags maximum

CH2 FINANCE:
  Line 1-2: The specific number that anchors the story
  Line 3:   "The full breakdown:" + one sentence
  Line 4:   Timestamps
  Line 5:   "Drop your thoughts below 👇"
  Line 6-7: 5 hashtags

CH3 CONSPIRACY:
  Line 1:   "The official story says X."
  Line 2:   "The documents say something different."
  Line 3:   One sentence teaser
  Line 4:   "Draw your own conclusions."
  Line 5-6: 5 hashtags — never use #conspiracy (flagged by YT)
            Use: #mystery #classified #untold #hidden #declassified

CH5 HISTORY:
  Line 1-2: The moment. The date. The consequence.
  Line 3:   "Full documentary:"
  Line 4:   Timestamps
  Line 5-6: 5 hashtags
```

### Upload timing — optimal per channel
```python
UPLOAD_SCHEDULE = {
    "CH1": {"days": ["MON","WED","FRI"], "time": "08:00"},   # Morning motivation
    "CH2": {"days": ["TUE","THU"],       "time": "07:00"},   # Pre-market
    "CH3": {"days": ["MON","THU"],       "time": "20:00"},   # Evening discovery
    "CH4": {"days": ["WED","SAT"],       "time": "09:00"},   # Weekend learning
    "CH5": {"days": ["TUE","SAT"],       "time": "19:00"},   # Evening documentary
}
```

### Shorts vs Long-form SEO differences
```
SHORTS:
  Title: MAX 7 words — gets cut on mobile otherwise
  Tags: focus on #Shorts and niche tags
  Description: 2 lines MAX — most viewers never see it
  Thumbnail: Less important — autoplay context matters more

LONG-FORM:
  Title: 7-10 words optimal
  Tags: full 13-tag strategy
  Description: full template above
  Thumbnail: CRITICAL — this is what drives the click
```

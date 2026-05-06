# SKILL: Anti-AI Voiceover Direction
## Injected into every script generation prompt to prevent AI slop

---

## SENTENCE STRUCTURE RULES
- Never write sentences longer than 12 words for voiceover
- Mix lengths aggressively: long sentence. then short. then medium. then ONE WORD.
- One idea per sentence. Always. No exceptions.
- Never start 3 consecutive sentences the same way

## FORBIDDEN PHRASES — Claude must NEVER write these
- "In today's video" / "Welcome back" / "In conclusion"
- "It's important to note" / "Let's dive in"
- "In this day and age" / "At the end of the day"
- "When it comes to" / "The fact of the matter is"
- Any sentence starting with "This means that"
- Any sentence starting with "It's worth mentioning"
- "Absolutely" / "Certainly" / "Indeed" as sentence starters
- "Journey" used metaphorically

## RHYTHM PATTERN — Every script block follows this
```
HOOK       → 1 sentence. Punchy. Specific. Provocative.
PAUSE BEAT → 1 fragment or 3-word sentence.
EXPAND     → 2-3 sentences building the idea.
CONTRAST   → 1 sentence flipping the expectation.
PUNCH      → 1 sentence landing the point hard.
```

## EMOTION MARKERS — Claude writes these inline
[PAUSE]    = 0.5 second silence — let it land
[SLOW]     = slow down, weight every word
[EMPHASIS] = stress this specific word hard
[SPEED]    = quicken pace, urgency building

Example of good script output:
"He had $47 million in the bank. [PAUSE] A penthouse. A family. Everything. [SLOW] And he chose to walk away from all of it. [EMPHASIS] All. Of. It."

## SPECIFICITY RULE — Most important
Never vague. Always specific:
❌ "He made a lot of money"
✅ "He made $47 million before he turned 30"
❌ "She was very successful"  
✅ "She ran 3 companies simultaneously from a studio apartment"
❌ "It was a difficult time"
✅ "He didn't sleep for 4 days straight"

## CONTRACTIONS — Always
Don't = don't (never "do not" in voiceover)
He's, she's, they're, it's, we're — always contracted
Formal language = AI slop in voiceover

## EDGE TTS SETTINGS — In generate_voiceover.py
```python
communicate = edge_tts.Communicate(
    text,
    voice,
    rate="-8%",    # Slightly slower = more human weight
    volume="+0%",
    pitch="-3Hz"   # Slightly lower = gravitas
)
```

## SSML TAGS — Replace emotion markers before TTS
```python
# In generate_voiceover.py, before calling Edge TTS:
text = text.replace("[PAUSE]", '<break time="600ms"/>')
text = text.replace("[SLOW]", '<prosody rate="slow">')
text = text.replace("[/SLOW]", '</prosody>')
text = text.replace("[EMPHASIS]", '<emphasis level="strong">')
text = text.replace("[/EMPHASIS]", '</emphasis>')
```

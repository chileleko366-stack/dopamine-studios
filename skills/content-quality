# SKILL: Anti-Slop Content & Storytelling
## Injected into generate_topics.py and write_render_jobs.py

---

## WHAT AI SLOP LOOKS LIKE — Never do this
- Generic motivational fluff: "Work hard and believe in yourself"
- Wikipedia summaries presented as insight  
- Numbered lists read aloud: "Number one... number two... number three"
- Every story arc the same: struggle → success → lesson
- Fake profundity: "Success is a journey, not a destination"
- Adjective overload: "incredible, life-changing, powerful, amazing"
- Telling instead of showing: "He was very determined"

---

## WHAT HIGH-END CONTENT LOOKS LIKE — Always do this

### STORY STRUCTURE — Use one of these, never the Wikipedia arc
```
1. IN MEDIAS RES — Start at the most intense moment, then explain
   "The day Kanye walked out of his $50M deal, he had $200 in his account"
   
2. REVERSAL — Start with what everyone believes, then destroy it
   "Everyone thinks Elon Musk is a genius. The data tells a different story."
   
3. HIDDEN DETAIL — The thing nobody talks about
   "Steve Jobs' real superpower had nothing to do with design"
   
4. BEFORE/AFTER — But make the before shocking
   "In 2008, he was sleeping in his car. The car was a Ferrari."
```

### THE HOOK FORMULA — First 30 seconds
Must contain ONE of:
- A specific number that surprises: "$340 million" / "47 days" / "age 23"
- A contradiction: rich but broke / famous but alone / winner but loser
- A direct challenge: "Everything you know about X is wrong"
- A cliffhanger: "What he did next destroyed his entire career"

Hook must NOT:
- Introduce yourself or the channel
- Explain what the video is about
- Ask the viewer to subscribe
- Use the word "today" in any context

---

## CLAUDE SCRIPT PROMPT — Full injection text

Add this entire block to every write_render_jobs.py Claude call:

```
CONTENT QUALITY RULES — non-negotiable:

SPECIFICITY: Every claim needs a specific detail.
Never: "He made a lot of money"
Always: "He cleared $12 million in 18 months"

SHOW DON'T TELL: Describe what happened, let viewer draw conclusion.
Never: "He was devastated by the loss"
Always: "He sat in his car for three hours after. Didn't make a call. Didn't move."

ONE STORY: Pick one person, one moment, one turning point. Go deep not wide.
Don't summarize a life — zoom into one decision that changed everything.

PACING: 
- First 30 seconds: hook so strong they can't leave
- Minutes 1-3: context and rising tension
- Minutes 3-7: the turning point in detail
- Final 2 minutes: the truth they didn't expect

SENTENCE VARIETY — alternate these patterns:
- Statement: "He quit."
- Question: "Why would anyone do that?"
- Contrast: "But that's not the whole story."
- Specificity: "Three weeks later, on a Tuesday morning..."

FORBIDDEN TRANSITIONS:
- "Moving on..."
- "Now let's talk about..."  
- "As we can see..."
- "This brings us to..."
Instead: just cut. Let the edit do the work.
```

---

## TOPIC QUALITY FILTER — In generate_topics.py

Before finalizing a topic, Claude must check against this:

```python
REJECTED_TOPIC_PATTERNS = [
    "how to be successful",
    "secrets of",
    "what they don't want you to know",  # overused
    "the truth about",                    # overused
    "you won't believe",                  # clickbait slop
    "mind blowing",
    "life changing",
    "motivational",                        # never describe it as motivational
]

GOOD_TOPIC_SIGNALS = [
    # Contains a specific name
    # Contains a specific number
    # Contains a contradiction or paradox
    # References a specific moment in time
    # Has a clear antagonist or obstacle
]
```

### Topic scoring — Claude rates topic 1-10 before using it
Criteria:
- Specific (not generic): +3 points
- Contains contradiction: +2 points  
- Unexpected angle: +2 points
- Strong visual potential: +2 points
- Click-worthy without being clickbait: +1 point
- Score below 7: regenerate

---

## SEO THAT DOESN'T FEEL LIKE SEO

### Title rules
- Never start with a number ("5 ways to...")
- Never use "Ultimate Guide"
- Optimal length: 6-10 words
- Must create curiosity gap without lying
- Test: would you personally click this?

### Description rules  
- First 2 lines must be compelling standalone (show before "more" cut)
- No keyword stuffing — write naturally
- Include 1 timestamp if long-form
- End with a question to drive comments

### Tags strategy
- 5 ultra-specific tags (exact topic)
- 5 medium tags (related topic)
- 3 broad tags (general category)
- Never repeat words from title in tags — YouTube already indexes those

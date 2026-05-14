"""
claude_client.py
Shared AI client for the pipeline.

Claude (Anthropic) is the primary provider for all script-generation calls.
Gemini is wrapped as a fallback that only fires if Claude returns an error
after 3 retries with exponential backoff.

Why this design:
- The channel bibles are tuned for Claude's writing style (precision, hedging,
  citation). Mixing providers per-channel would create inconsistent output.
- Gemini fallback exists only to prevent total pipeline failure if Anthropic
  is rate-limiting or having an outage. It is NOT a cost-optimisation path.
- To disable Gemini fallback entirely, delete _gemini_fallback() and remove
  the except block in generate(). The default behaviour will be Claude-only.

Usage:
    from claude_client import generate
    text = generate(
        system="You are a script writer.",
        user="Write a hook line about loneliness.",
        max_tokens=4096,
    )
"""

import os
import time
from typing import Optional

# Optional imports -- only required if the corresponding provider is used.
try:
    from anthropic import Anthropic, APIError, APIStatusError, APITimeoutError
    _CLAUDE_AVAILABLE = True
except ImportError:
    _CLAUDE_AVAILABLE = False

try:
    import google.generativeai as genai
    _GEMINI_AVAILABLE = True
except ImportError:
    _GEMINI_AVAILABLE = False


CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-4-7")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
ENABLE_GEMINI_FALLBACK = os.environ.get("ENABLE_GEMINI_FALLBACK", "true").lower() == "true"


def _log(msg: str):
    print(f"[claude_client] {msg}", flush=True)


def _claude_call(system: str, user: str, max_tokens: int, temperature: float) -> str:
    """Single Claude call. Raises on failure."""
    if not _CLAUDE_AVAILABLE:
        raise RuntimeError("anthropic package not installed; pip install anthropic")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    # Concatenate any text blocks in the response
    parts = []
    for block in response.content:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "".join(parts).strip()


def _gemini_fallback(system: str, user: str, max_tokens: int, temperature: float) -> str:
    """Gemini fallback. Only fires when Claude has failed."""
    if not _GEMINI_AVAILABLE:
        raise RuntimeError("google-generativeai not installed; pip install google-generativeai")
    if not os.environ.get("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY not set (required for fallback)")

    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel(GEMINI_MODEL)

    # Gemini doesn't have a separate `system` field in the same way.
    # We prepend it to the user prompt with clear framing.
    combined_prompt = f"[SYSTEM INSTRUCTIONS]\n{system}\n\n[TASK]\n{user}"

    response = model.generate_content(
        combined_prompt,
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
        ),
    )
    return response.text.strip()


def generate(
    system: str,
    user: str,
    max_tokens: int = 4096,
    temperature: float = 0.7,
    max_retries: int = 3,
) -> str:
    """
    Generate text using Claude with Gemini fallback.

    Args:
        system: System prompt (channel bible, role, constraints).
        user:   User prompt (the actual task).
        max_tokens: Maximum tokens in the response.
        temperature: Sampling temperature (0.0-1.0).
        max_retries: Claude retry count before falling back.

    Returns:
        The generated text, stripped.

    Raises:
        RuntimeError if both Claude and (if enabled) Gemini fail.
    """
    last_error: Optional[Exception] = None

    # Try Claude with exponential backoff
    for attempt in range(1, max_retries + 1):
        try:
            return _claude_call(system, user, max_tokens, temperature)
        except (APIStatusError, APITimeoutError, APIError) as e:
            last_error = e
            wait = 2 ** attempt  # 2, 4, 8 seconds
            _log(f"Claude attempt {attempt}/{max_retries} failed: {type(e).__name__}: {e}")
            if attempt < max_retries:
                _log(f"Retrying in {wait}s...")
                time.sleep(wait)
        except Exception as e:
            # Unknown error -- don't retry, escalate
            last_error = e
            _log(f"Claude unexpected error: {type(e).__name__}: {e}")
            break

    # Fallback to Gemini if enabled
    if ENABLE_GEMINI_FALLBACK:
        _log(f"All Claude attempts failed. Falling back to Gemini ({GEMINI_MODEL})...")
        try:
            return _gemini_fallback(system, user, max_tokens, temperature)
        except Exception as e:
            _log(f"Gemini fallback also failed: {type(e).__name__}: {e}")
            raise RuntimeError(
                f"Both Claude and Gemini failed. Claude error: {last_error}. Gemini error: {e}"
            )

    # Fallback disabled -- raise the Claude error
    raise RuntimeError(f"Claude failed after {max_retries} attempts and fallback is disabled: {last_error}")


def generate_json(
    system: str,
    user: str,
    max_tokens: int = 4096,
    temperature: float = 0.5,
    max_retries: int = 3,
) -> dict:
    """
    Like generate() but expects a JSON object in the response and returns it parsed.
    Strips common markdown code fences before parsing.
    """
    import json
    import re

    raw = generate(system, user, max_tokens, temperature, max_retries)

    # Strip code fences if present
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        _log(f"JSON parse failed. Raw output:\n{raw[:500]}")
        raise RuntimeError(f"AI response was not valid JSON: {e}")

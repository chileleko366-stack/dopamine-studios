"""
claude_client.py
Shared AI client for the pipeline.

Claude (Anthropic) is the primary provider for all script-generation calls.
Google Gemini is wrapped as a fallback that only fires if Claude returns an
error after 3 retries with exponential backoff.

Gemini SDK note: uses the current `google.genai` package (not the deprecated
`google.generativeai` which was sunset in 2025).
"""

import os
import time
from typing import Optional

try:
    from anthropic import Anthropic, APIError, APIStatusError, APITimeoutError
    _CLAUDE_AVAILABLE = True
except ImportError:
    _CLAUDE_AVAILABLE = False

try:
    from google import genai as google_genai
    from google.genai import types as genai_types
    _GEMINI_AVAILABLE = True
except ImportError:
    _GEMINI_AVAILABLE = False

CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-4-7")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
ENABLE_GEMINI_FALLBACK = os.environ.get("ENABLE_GEMINI_FALLBACK", "true").lower() == "true"


def _log(msg: str):
    print(f"[claude_client] {msg}", flush=True)


def _claude_call(system: str, user: str, max_tokens: int, temperature: float) -> str:
    if not _CLAUDE_AVAILABLE:
        raise RuntimeError("anthropic package not installed")
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
    parts = [block.text for block in response.content if getattr(block, "type", None) == "text"]
    return "".join(parts).strip()


def _gemini_fallback(system: str, user: str, max_tokens: int, temperature: float) -> str:
    if not _GEMINI_AVAILABLE:
        raise RuntimeError("google-genai not installed; pip install google-genai")
    if not os.environ.get("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY not set")

    client = google_genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    combined = f"[SYSTEM INSTRUCTIONS]\n{system}\n\n[TASK]\n{user}"
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=combined,
        config=genai_types.GenerateContentConfig(
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
    last_error: Optional[Exception] = None

    for attempt in range(1, max_retries + 1):
        try:
            return _claude_call(system, user, max_tokens, temperature)
        except (APIStatusError, APITimeoutError, APIError) as e:
            last_error = e
            wait = 2 ** attempt
            _log(f"Claude attempt {attempt}/{max_retries} failed: {type(e).__name__}: {e}")
            if attempt < max_retries:
                _log(f"Retrying in {wait}s...")
                time.sleep(wait)
        except Exception as e:
            last_error = e
            _log(f"Claude unexpected error: {type(e).__name__}: {e}")
            break

    if ENABLE_GEMINI_FALLBACK:
        _log(f"Claude failed. Falling back to Gemini ({GEMINI_MODEL})...")
        try:
            return _gemini_fallback(system, user, max_tokens, temperature)
        except Exception as e:
            _log(f"Gemini fallback failed: {type(e).__name__}: {e}")
            raise RuntimeError(
                f"Both providers failed. Claude: {last_error}. Gemini: {e}"
            )

    raise RuntimeError(f"Claude failed after {max_retries} attempts: {last_error}")


def generate_json(
    system: str,
    user: str,
    max_tokens: int = 4096,
    temperature: float = 0.5,
    max_retries: int = 3,
) -> dict:
    import json, re
    raw = generate(system, user, max_tokens, temperature, max_retries)
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        _log(f"JSON parse failed. Raw:\n{raw[:500]}")
        raise RuntimeError(f"AI response was not valid JSON: {e}")

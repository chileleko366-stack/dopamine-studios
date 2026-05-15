"""
claude_client.py

PRIMARY: Google Gemini free tier (gemini-1.5-flash)
FALLBACK: Anthropic API key
"""

import os
import json
import time
from typing import Optional

try:
            from anthropic import Anthropic, APIError, APIStatusError, APITimeoutError
            CLAUDEAPI_AVAILABLE = True
except ImportError:
            CLAUDEAPI_AVAILABLE = False

try:
            from google import genai as google_genai
            from google.genai import types as genai_types
            GEMINIAVAILABLE = True
except ImportError:
            GEMINIAVAILABLE = False

CLAUDE_MODEL           = os.environ.get("CLAUDE_MODEL", "claude-opus-4-6")
GEMINI_MODEL           = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
ENABLE_API_FALLBACK    = os.environ.get("ENABLE_API_FALLBACK", "true").lower() == "true"
ENABLE_GEMINI_FALLBACK = os.environ.get("ENABLE_GEMINI_FALLBACK", "true").lower() == "true"

def _log(msg: str):
            print(f"[claude_client] {msg}", flush=True)

def apicall(system: str, user: str, max_tokens: int, temperature: float) -> str:
            if not CLAUDEAPI_AVAILABLE:
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
    return "".join(b.text for b in response.content if getattr(b, "type", None) == "text").strip()

def geminicall(system: str, user: str, max_tokens: int, temperature: float) -> str:
            if not GEMINIAVAILABLE:
                            raise RuntimeError("google-genai not installed")
                        if not os.environ.get("GEMINI_API_KEY"):
                                        raise RuntimeError("GEMINI_API_KEY not set")
                                    client = google_genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    response = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=f"[SYSTEM]\n{system}\n\n[TASK]\n{user}",
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
            errors = []

    # 1. Try Gemini first (free tier)
    if ENABLE_GEMINI_FALLBACK and os.environ.get("GEMINI_API_KEY"):
                    _log(f"Using Gemini ({GEMINI_MODEL}) as primary provider...")
                    for attempt in range(1, max_retries + 1):
                                        try:
                                                                return geminicall(system, user, max_tokens, temperature)
except Exception as e:
                errors.append(f"Gemini/{attempt}: {e}")
                _log(f"Gemini attempt {attempt}/{max_retries} failed: {e}")
                if attempt < max_retries:
                                            time.sleep(2 ** attempt)

    # 2. Fall back to Anthropic API key
    if ENABLE_API_FALLBACK and os.environ.get("ANTHROPIC_API_KEY"):
                    _log("Falling back to Anthropic API key...")
                    for attempt in range(1, max_retries + 1):
                                        try:
                                                                return apicall(system, user, max_tokens, temperature)
except (APIStatusError, APITimeoutError, APIError) as e:
                errors.append(f"API/{attempt}: {e}")
                _log(f"API attempt {attempt}/{max_retries} failed: {e}")
                if attempt < max_retries:
                                            time.sleep(2 ** attempt)
except Exception as e:
                errors.append(f"API/unexpected: {e}")
                break

    raise RuntimeError("All providers failed:\n" + "\n".join(errors))

def generate_json(
            system: str,
            user: str,
            max_tokens: int = 4096,
            temperature: float = 0.5,
            max_retries: int = 3,
) -> dict:
            import re
    raw = generate(system, user, max_tokens, temperature, max_retries)
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
                    return json.loads(cleaned)
except json.JSONDecodeError as e:
        _log(f"JSON parse failed. Raw:\n{raw[:400]}")
        raise RuntimeError(f"Not valid JSON: {e}")

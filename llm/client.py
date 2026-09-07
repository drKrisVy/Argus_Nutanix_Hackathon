"""Thin wrapper around Groq's OpenAI-compatible chat completions endpoint.

Uses `requests` directly instead of the `groq` SDK to keep the dependency
footprint small. Reads the API key from the GROQ_API_KEY environment
variable -- never hardcode it here or anywhere else in this repo.
"""

import os
import time
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama-3.3-70b-versatile"


class LLMError(RuntimeError):
    pass


def chat(prompt, system=None, model=DEFAULT_MODEL, temperature=0.2, max_tokens=1024, retries=2):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise LLMError(
            "GROQ_API_KEY is not set. Copy .env.example to .env and add your key, "
            "or export GROQ_API_KEY in your shell."
        )

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    last_error = None
    for attempt in range(retries + 1):
        try:
            resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
            last_error = f"Groq API returned {resp.status_code}: {resp.text[:300]}"
        except requests.RequestException as e:
            last_error = str(e)
        time.sleep(1.5 * (attempt + 1))

    raise LLMError(f"Groq API call failed after {retries + 1} attempts: {last_error}")

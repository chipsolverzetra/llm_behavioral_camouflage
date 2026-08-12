"""
Provider-agnostic LLM wrapper + a small concurrency helper.

Key properties for the rigor run:
  - Routes to Anthropic or OpenAI(-compatible) by model name.
  - Does NOT send `temperature` (newer Claude models reject it).
  - Retries ONLY on transient errors (rate limit / timeout / 5xx) and FAILS FAST
    on client errors like a bad model name or auth — no more pointless 4x retries.
  - map_concurrent() runs many calls in parallel so 99 reps take minutes.
"""

from __future__ import annotations

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


def _status(exc):
    return getattr(exc, "status_code", None) or getattr(exc, "status", None)


def _should_retry(exc) -> bool:
    s = _status(exc)
    if s is None:
        return True            # network / unknown -> worth a retry
    if s == 429:
        return True            # rate limited -> back off and retry
    if 400 <= s < 500:
        return False           # client error (bad model, auth, request) -> don't hammer
    return True                # 5xx -> retry


def _retry(fn, *, attempts=4, base_delay=2.0):
    last = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            last = exc
            if not _should_retry(exc) or i == attempts - 1:
                raise
            wait = base_delay * (2 ** i)
            print(f"  [llm] transient error: {exc}. retry in {wait:.0f}s")
            time.sleep(wait)
    raise last


def call(model, system, user, *, max_tokens=1024) -> str:
    """Single-turn completion. Returns the model's text reply. No temperature."""
    name = model.lower()

    if "claude" in name:
        import anthropic

        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

        def _do():
            resp = client.messages.create(
                model=model,
                system=system,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": user}],
            )
            return "".join(b.text for b in resp.content if b.type == "text")

        return _retry(_do)

    from openai import OpenAI

    if any(t in name for t in ("gpt", "o1", "o3", "o4")):
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    else:
        base = os.environ.get("OPENAI_COMPAT_BASE_URL")
        if not base:
            raise RuntimeError(f"No provider configured for model '{model}'.")
        client = OpenAI(api_key=os.environ.get("OPENAI_COMPAT_API_KEY", "x"), base_url=base)

    def _do():
        resp = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return resp.choices[0].message.content or ""

    return _retry(_do)


def _extract_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    a, b = text.find("{"), text.rfind("}")
    return text[a : b + 1] if a != -1 and b != -1 and b > a else text


def call_json(model, system, user, *, max_tokens=1024, attempts=3) -> dict:
    last = None
    for _ in range(attempts):
        raw = call(model, system, user, max_tokens=max_tokens)
        try:
            return json.loads(_extract_json(raw))
        except json.JSONDecodeError as exc:
            last = exc
            user = user + "\n\nReply with ONLY a valid JSON object, nothing else."
    raise RuntimeError(f"No valid JSON from {model}: {last}")


def map_concurrent(fn, items, *, max_workers=12):
    """Run fn over items in parallel. A permanently-failed item becomes None."""
    results = [None] * len(items)

    def _safe(i, it):
        try:
            return i, fn(it)
        except Exception as exc:  # noqa: BLE001
            print(f"  [llm] item {i} failed permanently: {exc}")
            return i, None

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = [ex.submit(_safe, i, it) for i, it in enumerate(items)]
        done = 0
        for fut in as_completed(futs):
            i, val = fut.result()
            results[i] = val
            done += 1
            if done % 25 == 0 or done == len(items):
                print(f"    ...{done}/{len(items)} done")
    return results

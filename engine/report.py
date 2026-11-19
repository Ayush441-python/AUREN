import json
import re

import requests

from engine.env import load_env, setting

load_env()

SYSTEM = (
    "You are a risk analyst writing for a beginner investor. "
    "Use ONLY the numbers in the JSON you are given and never invent new numbers. "
    "Explain the 3 biggest risks and why each matters, in short paragraphs. "
    "Then list general ways people reduce these kinds of risk. "
    "Never tell the user to buy or sell any specific asset. "
    "End with: 'Analytics only, not investment advice. Past data does not predict the future.'"
)

NUM = re.compile(r"\d+(?:,\d{3})*(?:\.\d+)?")


def clean_output(text: str) -> str:
    """Remove <think>...</think> blocks that some open models add."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    if "</think>" in text:
        text = text.rsplit("</think>", 1)[1]
    if "<think>" in text:
        text = text.split("<think>", 1)[0]
    return text.strip()


def ai_report(metrics: dict, base_url: str, api_key: str, model: str,
              timeout: int = 120) -> str:
    """Call any OpenAI-compatible chat endpoint (Groq, Ollama, OpenRouter, ...)."""
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    user = SYSTEM + "\n\nPortfolio metrics JSON:\n" + json.dumps(metrics, default=str)
    reasoning = "gpt-oss" in (model or "") or "groq.com" in (base_url or "")
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": user}],
    }
    if reasoning:
        # gpt-oss spends tokens on thinking; max_tokens can leave content empty
        payload["max_completion_tokens"] = 4096
        payload["include_reasoning"] = False
        payload["temperature"] = 0.6
    else:
        payload["temperature"] = 0.2
        payload["max_tokens"] = 1500
        payload["messages"] = [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps(metrics, default=str)},
        ]
    effort = setting("LLM_REASONING_EFFORT")
    if effort:
        payload["reasoning_effort"] = effort
    r = requests.post(base_url.rstrip("/") + "/chat/completions",
                      json=payload, headers=headers, timeout=timeout)
    if not r.ok:
        detail = r.text.strip()[:400]
        raise RuntimeError(f"LLM HTTP {r.status_code}: {detail or r.reason}")
    choice = r.json()["choices"][0]
    if choice.get("finish_reason") == "length":
        raise RuntimeError(
            "The model hit the token limit before finishing the report. Try again or raise the limit."
        )
    msg = choice["message"]
    text = clean_output(msg.get("content") or "")
    if not text:
        raise RuntimeError("The model returned an empty answer")
    return text


def _numbers(text: str) -> list[float]:
    return [float(m.replace(",", "")) for m in NUM.findall(text)]


def unverified_numbers(report: str, metrics: dict) -> list[float]:
    """Numbers in the report that do not appear in the metrics JSON.
    Fractions count as matching their percentage (0.34 matches 34).
    Small whole numbers (1-10) and 100 are ignored."""
    allowed = set()
    for v in _numbers(json.dumps(metrics, default=str)):
        allowed.add(v)
        allowed.add(v * 100)
    bad = []
    for v in _numbers(report):
        if v == int(v) and (v <= 10 or v == 100):
            continue
        if not any(abs(v - a) <= 0.51 for a in allowed):
            bad.append(v)
    return bad
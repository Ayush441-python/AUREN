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
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def _sanitize_for_report(metrics: dict) -> dict:
    """Strip massive timeseries and chart data before sending to LLM.
    
    The raw analysis object contains hundreds of daily points across
    `price_series`, `drawdown_series`, and `dates` (~35,000+ chars), which
    causes rate-limit / TPM 413 errors on Groq / LLM providers.
    The narrative only requires core risk metrics, stress tests, exposures, and reasons.
    """
    if not isinstance(metrics, dict):
        return metrics
    # Drop timeseries fields
    chart_keys = {"price_series", "drawdown_series", "dates"}
    cleaned = {k: v for k, v in metrics.items() if k not in chart_keys}
    return cleaned


def ai_report(metrics: dict, base_url: str, api_key: str, model: str,
              timeout: int = 120) -> str:
    """Call any OpenAI-compatible chat endpoint (Groq, Ollama, OpenRouter, ...)."""
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    clean_metrics = _sanitize_for_report(metrics)
    user = SYSTEM + "\n\nPortfolio metrics JSON:\n" + json.dumps(clean_metrics, default=str)
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
            {"role": "user", "content": json.dumps(clean_metrics, default=str)},
        ]
    effort = setting("LLM_REASONING_EFFORT")
    if effort:
        payload["reasoning_effort"] = effort
    r = requests.post(base_url.rstrip("/") + "/chat/completions",
                      json=payload, headers=headers, timeout=timeout)
    if not r.ok:
        detail = r.text.strip()[:400]
        raise RuntimeError(f"LLM HTTP {r.status_code}: {detail or r.reason}")
    msg = r.json()["choices"][0]["message"]
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
    portfolio_val = metrics.get("portfolio_value_usd", 0.0)

    def _collect(obj):
        if isinstance(obj, dict):
            # Inspect dictionary values ONLY, avoiding metric keys like 'correlated_pairs_above_0.7'
            for v in obj.values():
                _collect(v)
        elif isinstance(obj, (list, tuple, set)):
            for v in obj:
                _collect(v)
        elif isinstance(obj, str):
            # Pre-formatted percentage/count strings like "Largest holding is 40% (over 30%)"
            for v in _numbers(obj):
                allowed.add(v)
        elif isinstance(obj, (int, float)):
            val = float(obj)
            allowed.add(val)
            # Only ratios/fractions representing shares or percentages (in [-1.0, 1.0]) are scaled by 100
            if 0.0 < abs(val) <= 1.0:
                allowed.add(round(val * 100, 4))
                allowed.add(round(abs(val) * 100, 4))
                if portfolio_val > 0:
                    allowed.add(round(abs(val) * portfolio_val, 2))

    _collect(metrics)
    bad = []
    for v in _numbers(report):
        if v == int(v) and (v <= 10 or v == 100):
            continue
        if not any(abs(v - a) <= 0.51 for a in allowed):
            bad.append(v)
    return bad
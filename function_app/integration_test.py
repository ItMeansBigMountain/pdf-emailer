# function_app/integration_test.py
import os
import sys
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

def base_url() -> str:
    """
    Accepts:
      AZURE_FUNCTION_BASE_URL="pdf-emailer-func.azurewebsites.net"
      or "https://pdf-emailer-func.azurewebsites.net"
      or "http://localhost:7071"
    Fallback: http://localhost:7071
    """
    raw = (os.getenv("AZURE_FUNCTION_BASE_URL") or "").strip()
    if not raw:
        return "http://localhost:7071"
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw.rstrip("/")
    return "https://" + raw.rstrip("/")

def function_url(route: str = "/api/generate-newsletter") -> str:
    url = f"{base_url()}{route}"
    key = (os.getenv("AZURE_FUNCTION_KEY") or "").strip()
    if key:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}code={key}"
    return url

def build_payload() -> dict:
    """
    Always forces web search + email send.
    Customize via env:
      TEST_NICHE, TEST_SOURCES, TEST_TITLE, TEST_AUDIENCE, TEST_TONE,
      TEST_CTA, TEST_CTA_NOTE, TEST_MODEL, TEST_TEMPERATURE, TEST_MAX_TURNS,
      TEST_RECIPIENTS
    """
    niche   = os.getenv("TEST_NICHE", "crypto: BTC/ETH, DeFi, regulation, on-chain data")
    sources = os.getenv(
        "TEST_SOURCES",
        "coindesk.com,cointelegraph.com,decrypt.co,reuters.com,bloomberg.com"
    )
    model   = os.getenv("TEST_MODEL", os.getenv("LLM_MODEL", "gpt-4o-2024-08-06"))

    recipients = os.getenv("TEST_RECIPIENTS", os.getenv("EMAIL_RECIPIENTS", "")).strip()

    return {
        "allow_web": True,
        "send_email": True,  # <- force email send during test
        "recipients": recipients if recipients else None,  # function will fallback to env if None
        "sources": [s.strip() for s in sources.split(",") if s.strip()],
        "topic": niche,
        "title": os.getenv("TEST_TITLE", "Crypto Weekly"),
        "audience": os.getenv("TEST_AUDIENCE", "operators"),
        "tone": os.getenv("TEST_TONE", "concise"),
        "cta": os.getenv("TEST_CTA", "Read the full brief"),
        "cta_note": os.getenv("TEST_CTA_NOTE", "3-minute skim"),
        "model": model,
        "temperature": float(os.getenv("TEST_TEMPERATURE", "0.2")),
        "max_turns": int(os.getenv("TEST_MAX_TURNS", "1")),
        "custom_prompt": os.getenv("TEST_CUSTOM_PROMPT", ""),
    }

def post_json(url: str, payload: dict, timeout_s: int) -> requests.Response:
    return requests.post(url, json=payload, timeout=timeout_s)

def validate_response(data: dict) -> None:
    # Hard validations — raise AssertionError on failure
    if not isinstance(data, dict):
        raise AssertionError(f"Response is not a JSON object: {type(data)}")

    for k in ("status", "subject", "text", "html"):
        if k not in data:
            raise AssertionError(f"Missing key in response: '{k}'")
        if k == "status":
            if data[k] != "ok":
                raise AssertionError(f"Unexpected status: {data[k]}")
        else:
            if not isinstance(data[k], str) or not data[k].strip():
                raise AssertionError(f"Key '{k}' must be a non-empty string")

    # Sources can come either from the model (structured outputs) or annotations, but must be present
    sources = data.get("sources", [])
    scount = data.get("sources_count", len(sources))
    if not isinstance(sources, list):
        raise AssertionError(f"'sources' must be a list, got: {type(sources)}")

    if scount < 1:
        raise AssertionError(
            f"No sources captured. Got sources_count={scount}, sources len={len(sources)}"
        )

    # Each source item should minimally have a URL
    bad = [s for s in sources if not isinstance(s, dict) or not str(s.get("url", "")).strip()]
    if bad:
        raise AssertionError(f"Found source items without 'url': {json.dumps(bad[:3])}")

def main() -> int:
    url = function_url()
    payload = build_payload()
    timeout = int(os.getenv("TEST_TIMEOUT", "90"))
    retries = int(os.getenv("TEST_RETRIES", "1"))  # minimal retry once if 500 or empty sources

    last_exc: Exception | None = None
    for attempt in range(1, retries + 2):
        try:
            resp = post_json(url, payload, timeout)
            text = resp.text

            if resp.status_code != 200:
                raise AssertionError(f"HTTP {resp.status_code}: {text}")

            # Must be JSON
            try:
                data = resp.json()
            except Exception:
                raise AssertionError(f"Response is not JSON: {text[:500]}")

            validate_response(data)
            # Success
            return 0

        except (AssertionError, requests.RequestException) as e:
            last_exc = e
            if attempt <= retries:
                # brief backoff then try again
                time.sleep(2.0)
                continue
            raise

    # Shouldn't reach here
    if last_exc:
        raise last_exc
    return 1

if __name__ == "__main__":
    sys.exit(main())

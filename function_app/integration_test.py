# function_app/integration_test.py
import os, sys, json, requests
from dotenv import load_dotenv
load_dotenv()

def base_url() -> str:
    raw = (os.getenv("AZURE_FUNCTION_BASE_URL") or "").strip()
    if not raw:
        return "http://localhost:7071"
    return raw.rstrip("/") if raw.startswith("http") else "https://" + raw.rstrip("/")

def function_url(route="/api/generate-newsletter") -> str:
    url = f"{base_url()}{route}"
    key = (os.getenv("AZURE_FUNCTION_KEY") or "").strip()
    if key:
        url += ("&" if "?" in url else "?") + f"code={key}"
    return url

def build_payload() -> dict:
    sources = os.getenv("TEST_SOURCES", "reuters.com,theverge.com,ft.com")
    return {
        "allow_web": True,
        "send_email": True,
        "sources": [s.strip() for s in sources.split(",") if s.strip()],
        "topic": os.getenv("TEST_NICHE", "crypto: BTC/ETH, DeFi, regulation, on-chain data"),
        "title": os.getenv("TEST_TITLE", "Crypto Weekly"),
        "audience": os.getenv("TEST_AUDIENCE", "operators"),
        "tone": os.getenv("TEST_TONE", "concise"),
        "cta": os.getenv("TEST_CTA", "Read the full brief"),
        "cta_note": os.getenv("TEST_CTA_NOTE", "3-minute skim"),
        "model": os.getenv("LLM_MODEL", "gpt-4o-2024-08-06"),
        "temperature": float(os.getenv("TEST_TEMPERATURE", "0.2")),
        "max_turns": int(os.getenv("TEST_MAX_TURNS", "2")),
        "custom_prompt": os.getenv("TEST_CUSTOM_PROMPT", ""),
    }

def main():
    url = function_url()
    payload = build_payload()
    timeout = int(os.getenv("TEST_TIMEOUT", "90"))
    resp = requests.post(url, json=payload, timeout=timeout)
    if resp.status_code != 200:
        raise AssertionError(f"HTTP {resp.status_code}: {resp.text}")

    try:
        data = resp.json()
    except Exception:
        raise AssertionError(f"Non-JSON response: {resp.text[:500]}")

    for k in ("subject", "text", "html"):
        v = data.get(k)
        if not isinstance(v, str) or not v.strip():
            raise AssertionError(f"Missing/empty key: {k}")

    sources = data.get("sources", [])
    scount = data.get("sources_count", len(sources))
    if scount < 1:
        raise AssertionError(f"No sources were captured. Response: {json.dumps(data)[:800]}")

    # Optional: send_email must have been requested
    if not payload.get("send_email", True):
        raise AssertionError("send_email was not true in payload")

    # Looks good
    return 0

if __name__ == "__main__":
    sys.exit(main())

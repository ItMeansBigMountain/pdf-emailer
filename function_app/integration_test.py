import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv()

def base_url() -> str:
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
    # Always use web search. Swap sources/topic per niche as needed.
    niche = os.getenv("TEST_NICHE", "crypto: BTC/ETH, DeFi, regulation, on-chain data")
    sources = os.getenv("TEST_SOURCES", "coindesk.com,cointelegraph.com,decrypt.co,reuters.com,bloomberg.com")
    model = os.getenv("LLM_MODEL", "gpt-4o-2024-08-06")

    return {
        "allow_web": True,
        "send_email": True, 
        "sources": [s.strip() for s in sources.split(",") if s.strip()],
        "topic": niche,
        "title": os.getenv("TEST_TITLE", "Crypto Weekly"),
        "audience": os.getenv("TEST_AUDIENCE", "operators"),
        "tone": os.getenv("TEST_TONE", "concise"),
        "cta": os.getenv("TEST_CTA", "Read the full brief"),
        "cta_note": os.getenv("TEST_CTA_NOTE", "3-minute skim"),
        "model": model,
        "temperature": float(os.getenv("TEST_TEMPERATURE", "0.2")),
        "max_turns": int(os.getenv("TEST_MAX_TURNS", "2")),
        # optional: pass any custom extra copy to fold into the newsletter
        "custom_prompt": os.getenv("TEST_CUSTOM_PROMPT", ""),
    }

def main():
    url = function_url()
    payload = build_payload()
    timeout = int(os.getenv("TEST_TIMEOUT", "60"))

    print(f"POST {url}")
    print(f"Payload sources: {payload['sources']}")

    resp = requests.post(url, json=payload, timeout=timeout)
    print(f"HTTP {resp.status_code}")

    # Fail fast if not JSON
    resp.raise_for_status()
    data = resp.json()

    # Minimal sanity checks for your structured output
    for k in ("status", "subject", "text", "html"):
        if k not in data or not isinstance(data[k], str) or not data[k].strip():
            print(f"Missing/empty key in response: {k}")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            sys.exit(2)

    sources = data.get("sources", [])
    scount = data.get("sources_count", len(sources))
    print("\n=== Test Summary ===")
    print(f"Subject      : {data['subject'][:120]}")
    print(f"Sources found: {scount}")
    if sources:
        for i, s in enumerate(sources[:5], 1):
            print(f"  {i}. {s.get('url','')}")

    # Hard assertion: must have at least one source annotation
    if scount < 1:
        print("\nNo sources were captured. Check domains, model snapshot, or web_search tool availability.")
        sys.exit(3)

    print("\nPASS ✅")

if __name__ == "__main__":
    try:
        main()
    except requests.RequestException as e:
        print(f"Network/HTTP error: {e}")
        sys.exit(1)

import os
import json
import sys
import requests
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

def build_base_url() -> str:
    """
    Accepts:
      AZURE_FUNCTION_BASE_URL = "pdf-emailer-func.azurewebsites.net"
      or "https://pdf-emailer-func.azurewebsites.net"
      or "http://localhost:7071"
    Fallback: http://localhost:7071
    """
    raw = os.getenv("AZURE_FUNCTION_BASE_URL", "").strip()
    if not raw:
        return "http://localhost:7071"
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw.rstrip("/")
    return "https://" + raw.rstrip("/")

def build_function_url(base_url: str, route: str = "/api/generate-newsletter") -> str:
    url = f"{base_url}{route}"
    func_key = os.getenv("AZURE_FUNCTION_KEY", "").strip()
    if func_key:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}code={func_key}"
    return url

# ---------- Choose your payload ----------

def get_newsletter_payload() -> dict:
    """Original marketing email payload (no web search)."""
    return {
        "provider": "openai",
        "model": os.getenv("LLM_MODEL", "gpt-4o-mini"),
        "temperature": 0.7,
        "title": "🏆 Recover Faster, Train Harder",
        "audience": "martial artists looking to boost recovery",
        "stats": "studies show 85% of athletes improved recovery with supplements",
        "tone": "witty and hype",
        "cta": "Listen to our podcast for more insights",
        "cta_note": "like and subscribe to our social media",
        "custom_prompt": "write a newsletter for a martial arts gym",
        "recipients": "trapiistan@gmail.com,classicalechos@gmail.com",
    }

def get_websearch_payload() -> dict:
    """
    Web-search variant. Your function should honor allow_web + sources.
    Update sources/topic as needed.
    """
    return {
        "allow_web": True,
        "sources": ["reuters.com", "theverge.com", "ft.com"],
        "topic": "crypto: BTC, ETH, ETFs, DeFi",
        "title": "Crypto Weekly",
        "audience": "operators",
        "tone": "concise",
        "cta": "Read the full brief",
        "cta_note": "3-minute skim",
        "model": os.getenv("LLM_MODEL", "gpt-4o-mini"),
        "temperature": 0.3,
        "max_turns": 2
    }

def post_json(url: str, payload: dict, timeout_s: int = 30) -> requests.Response:
    return requests.post(url, json=payload, timeout=timeout_s)

def main():
    base = build_base_url()
    url = build_function_url(base)

    # Pick your poison. If your deployed function supports web search, use get_websearch_payload().
    # Otherwise use get_newsletter_payload().
    payload = get_websearch_payload()  # or: get_newsletter_payload()

    try:
        resp = post_json(url, payload)
        print(f"HTTP {resp.status_code} from {url}")

        ct = resp.headers.get("content-type", "")
        if "application/json" in ct.lower():
            try:
                data = resp.json()
            except Exception:
                # Some Functions return text with JSON inside. Try a salvage parse.
                data = json.loads(resp.text)
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            # Raw text fallback (e.g., your Function returns a plain HttpResponse body)
            print(resp.text)

        # Basic assertion to fail fast in CI
        if resp.status_code != 200:
            sys.exit(1)

    except requests.exceptions.Timeout:
        print("Timeout talking to your function. It shouldn’t take this long.")
        sys.exit(2)
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        sys.exit(3)

if __name__ == "__main__":
    main()

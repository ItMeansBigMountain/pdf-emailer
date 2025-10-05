import os
import json
import requests
from typing import List

# --- Configuration helpers ---------------------------------------------------

def _env(name: str, default: str = "") -> str:
    v = os.getenv(name)
    return v if v is not None else default

def base_url() -> str:
    """
    Resolved priority:
      1) AZURE_FUNCTION_BASE_URL (can be full https://... or host only)
      2) https://pdf-emailer-func.azurewebsites.net  (production)
      3) http://localhost:7071                        (fallback)
    """
    raw = (_env("AZURE_FUNCTION_BASE_URL").strip())
    if raw:
        if raw.startswith("http://") or raw.startswith("https://"):
            return raw.rstrip("/")
        return "https://" + raw.rstrip("/")
    # Prefer prod unless explicitly testing locally
    if _env("LOCAL_TEST", "").lower() in ("1", "true", "yes"):
        return "http://localhost:7071"
    return "https://pdf-emailer-func.azurewebsites.net"

def function_url(route: str = "/api/generate-newsletter") -> str:
    url = f"{base_url()}{route}"
    key = _env("AZURE_FUNCTION_KEY").strip()
    if key:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}code={key}"
    return url

# --- Payload builder (always web search) -------------------------------------

def build_payload() -> dict:
    """
    Always searches the web with allowed domains, and sends the email.
    Customize via env:
      TEST_NICHE, TEST_SOURCES (comma-separated), TEST_TITLE, TEST_AUDIENCE,
      TEST_TONE, TEST_CTA, TEST_CTA_NOTE, LLM_MODEL, TEST_TEMPERATURE, TEST_MAX_TURNS,
      TEST_CUSTOM_PROMPT, TEST_RECIPIENTS
    """
    niche = _env("TEST_NICHE", "crypto: BTC/ETH, DeFi, regulation, on-chain data")
    sources_csv = _env(
        "TEST_SOURCES",
        "coindesk.com,cointelegraph.com,decrypt.co,reuters.com,bloomberg.com",
    )
    sources: List[str] = [s.strip() for s in sources_csv.split(",") if s.strip()]

    recipients = _env("TEST_RECIPIENTS", _env("EMAIL_RECIPIENTS", ""))  # optional

    payload = {
        "allow_web": True,
        "send_email": True,
        "sources": sources,
        "topic": niche,
        "title": _env("TEST_TITLE", "Crypto Weekly"),
        "audience": _env("TEST_AUDIENCE", "operators"),
        "tone": _env("TEST_TONE", "concise"),
        "cta": _env("TEST_CTA", "Read the full brief"),
        "cta_note": _env("TEST_CTA_NOTE", "3-minute skim"),
        "model": _env("LLM_MODEL", "gpt-4o-2024-08-06"),
        "temperature": float(_env("TEST_TEMPERATURE", "0.2")),
        "max_turns": int(_env("TEST_MAX_TURNS", "2")),
        "custom_prompt": _env("TEST_CUSTOM_PROMPT", ""),
    }

    if recipients:
        payload["recipients"] = recipients

    return payload

# --- Test runner -------------------------------------------------------------

def main() -> int:
    url = function_url()
    payload = build_payload()
    timeout = int(_env("TEST_TIMEOUT", "90"))

    # 1) Call the function
    try:
        resp = requests.post(url, json=payload, timeout=timeout)
    except requests.Timeout as e:
        raise TimeoutError(f"Timeout talking to Azure Function at {url}") from e
    except requests.RequestException as e:
        raise ConnectionError(f"Network error calling {url}: {e}") from e

    # 2) Fail if non-200
    if resp.status_code != 200:
        # Try to include server-provided JSON if possible for easier debugging
        text = resp.text
        try:
            parsed = resp.json()
            text = json.dumps(parsed, indent=2, ensure_ascii=False)
        except Exception:
            pass
        raise AssertionError(f"HTTP {resp.status_code}: {text}")

    # 3) Must be JSON
    try:
        data = resp.json()
    except Exception as e:
        raise ValueError(f"Non-JSON response from function: {resp.text[:500]}") from e

    # 4) Validate keys and shape
    for k in ("status", "subject", "text", "html"):
        if k not in data:
            raise AssertionError(f"Missing key in response: {k}")
        if k in ("subject", "text", "html"):
            v = data[k]
            if not isinstance(v, str) or not v.strip():
                raise AssertionError(f"Empty or non-string value for '{k}'")

    # 5) Sources should be present (at least 1)
    sources = data.get("sources", [])
    scount = data.get("sources_count", len(sources))
    if scount < 1 or not isinstance(sources, list):
        raise AssertionError(
            f"No sources captured. Got sources_count={scount}, sources type={type(sources).__name__}"
        )

    # 6) Optional check: email status
    email_status = data.get("email_status", "unknown")
    if payload.get("send_email") and email_status not in ("sent", "skipped"):
        # We only fail if it's neither sent nor skipped (i.e., "error" or unknown)
        email_error = data.get("email_error")
        raise AssertionError(f"Email send failed. status={email_status}, error={email_error}")

    return 0


if __name__ == "__main__":
    # Let exceptions bubble up—CI will mark the job failed with the traceback.
    exit(main())

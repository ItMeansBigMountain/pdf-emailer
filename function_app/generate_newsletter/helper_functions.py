# helper_functions.py (patched final)

import os
import re
import json
import smtplib
import logging
from typing import List, Dict, Optional
from email.message import EmailMessage

from pydantic import BaseModel, Field
from markdown2 import markdown

# -----------------------------------------------------------------------------
# System instructions: force inline sources and JSON-only output
# -----------------------------------------------------------------------------
SYSTEM_INSTRUCTIONS = (
    "You are a senior newsletter editor.\n"
    "You have the web_search tool enabled. Use it ONLY to fetch RECENT articles (last 7–14 days) "
    "from the allowed domains provided by the user. If you cannot find a verified article for a claim, say so.\n"
    "Every bullet or claim MUST include an inline source link in parentheses exactly like "
    "(Source: https://allowed-domain/...), using the original article URL. "
    "Do not use footnote numbers. Do not summarize without sources. Do not invent URLs.\n"
    "Return ONLY JSON matching the schema. Do NOT include markdown fences. Do NOT include prose."
)

# -----------------------------------------------------------------------------
# Structured Output model (we validate after parsing raw JSON)
# -----------------------------------------------------------------------------
class NewsletterPayload(BaseModel):
    subject: str = Field(..., max_length=78, description="Email subject, <=78 chars.")
    text: str = Field(..., description="Plaintext body for clients without HTML.")
    html: str = Field(..., description="Inline-friendly HTML, no external CSS/scripts.")

# -----------------------------------------------------------------------------
# Prompt construction
# -----------------------------------------------------------------------------
def _build_user_task(
    audience: str,
    tone: str,
    title: str,
    cta: str,
    cta_note: str,
    custom_prompt: str,
    topic: Optional[str],
    sources: List[str],
) -> str:
    src_lines = "\n".join(f"- {d}" for d in sources)
    topic_line = f"Topic focus: {topic}" if topic else "Topic focus: latest noteworthy items"
    return (
        f"{topic_line}\nAllowed domains only:\n{src_lines}\n\n"
        f"Audience: {audience}\nTone: {tone}\nTitle: {title}\n"
        f"CTA label: {cta}\nCTA note: {cta_note}\nExtra instructions: {custom_prompt}\n"
        "Tasks:\n"
        "1) Use the web_search tool to find the most recent, high-signal articles from ONLY the allowed domains.\n"
        "2) Synthesize a concise newsletter. Each bullet/statement MUST end with \"(Source: https://...)\" "
        "linking the original article URL from an allowed domain.\n"
        "3) Return only the structured object defined by the schema (subject, text, html). No extra keys.\n"
        "4) Include sources inline in text/html; also include standard message annotations (URLs)."
    )

# -----------------------------------------------------------------------------
# OpenAI client + JSON schema for Structured Outputs
# -----------------------------------------------------------------------------
def _get_openai_client():
    from openai import OpenAI
    # OPENAI_API_KEY must be set in environment (Functions config/app settings)
    return OpenAI()

def _json_schema() -> dict:
    # 'sources' is NOT part of the schema; we attach it after validation.
    return {
        "type": "object",
        "properties": {
            "subject": {"type": "string", "description": "Email subject, <=78 chars."},
            "text": {"type": "string", "description": "Plaintext body."},
            "html": {"type": "string", "description": "Inline-safe HTML only."},
        },
        "required": ["subject", "text", "html"],
        "additionalProperties": False,
    }

# -----------------------------------------------------------------------------
# Source harvesting: first from annotations, then fallback from HTML
# -----------------------------------------------------------------------------
def _extract_sources_from_resp(resp) -> List[Dict[str, str]]:
    """
    Harvest URL annotations from the last assistant message (if present).
    Returns: [{"title": "...", "url": "...", "source": ""}, ...]
    """
    items = [it for it in getattr(resp, "output", []) if getattr(it, "type", "") == "message"]
    if not items:
        return []
    last = items[-1]
    out: List[Dict[str, str]] = []
    for block in getattr(last, "content", []) or []:
        for ann in getattr(block, "annotations", []) or []:
            if getattr(ann, "type", "") == "url" and getattr(ann, "url", ""):
                out.append(
                    {
                        "title": getattr(ann, "title", "") or "",
                        "url": ann.url,
                        "source": "",
                    }
                )
    return out

_URL_RE = re.compile(r'https?://[^\s")]+', re.IGNORECASE)

def _extract_urls_from_html(html: str) -> List[str]:
    if not html:
        return []
    # de-dupe while keeping order
    return list(dict.fromkeys(_URL_RE.findall(html)))

def _filter_allowed(urls: List[str], allowed_domains: List[str]) -> List[str]:
    """
    Keep only URLs that belong to one of the allowed domains.
    Accepts http/https and basic endswith/startswith checks.
    """
    result: List[str] = []
    for u in urls:
        lu = u.lower()
        for d in allowed_domains:
            d = d.strip().lower()
            if not d:
                continue
            if lu.startswith(f"https://{d}/") or lu.startswith(f"http://{d}/") or lu.endswith(d):
                result.append(u)
                break
    # final de-dupe
    out: List[str] = []
    seen = set()
    for u in result:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out

# -----------------------------------------------------------------------------
# Main generator
# -----------------------------------------------------------------------------
def generate_newsletter_via_openai_websearch(
    audience: str,
    tone: str,
    title: str,
    cta: str,
    cta_note: str,
    custom_prompt: str,
    sources: List[str],
    topic: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.2,
    max_turns: int = 1,
) -> Dict:
    """
    Uses OpenAI Responses API with web_search tool and Structured Outputs (json_schema) to
    produce a newsletter payload (subject, text, html). Then harvests sources either
    from annotations or from the HTML as fallback (filtered to the allowlist).
    """
    if not sources:
        raise ValueError("Provide at least one domain in `sources`")

    # So we can reference the original allowlist later when filtering fallback URLs.
    sources_param = sources[:]

    client = _get_openai_client()
    model = model or os.getenv("LLM_MODEL", "gpt-4o-2024-08-06")
    schema = _json_schema()
    user_input = _build_user_task(audience, tone, title, cta, cta_note, custom_prompt, topic, sources_param)

    logging.info("[generate] model=%s, temperature=%s, allowlist=%s", model, temperature, sources_param)

    # Turn 1: allow web_search + enforce json_schema
    resp = client.responses.create(
        model=model,
        temperature=temperature,
        max_output_tokens=1500,
        instructions=SYSTEM_INSTRUCTIONS,
        input=[{"role": "user", "content": user_input}],
        tools=[{"type": "web_search"}],
        tool_choice="auto",
        text={
            "format": {
                "type": "json_schema",
                "name": "newsletter_payload",
                "schema": schema,
                "strict": True,
            }
        },
    )

    # If the model performed a tool call and didn't produce the JSON yet,
    # do a finalize pass with tools disabled.
    if not getattr(resp, "output_text", None) and max_turns > 0:
        logging.warning("[generate] First turn produced no output_text; finalizing JSON without tools.")
        resp = client.responses.create(
            model=model,
            temperature=0.1,
            max_output_tokens=1500,
            instructions="Return ONLY the JSON object for keys subject, text, html. Nothing else.",
            input=[{"role": "user", "content": "Finalize JSON now."}],
            tools=[{"type": "web_search"}],
            tool_choice="none",
            text={
                "format": {
                    "type": "json_schema",
                    "name": "newsletter_payload",
                    "schema": schema,
                    "strict": True,
                }
            },
        )

    # Try to parse the JSON directly. If it fails, ask once more for the pure JSON.
    try:
        raw_text = resp.output_text or ""
        logging.info("[generate] output_text length=%d", len(raw_text))
        payload = json.loads(raw_text)
    except Exception as e:
        logging.error("[generate] JSON parse failed on first attempt: %s", e)
        resp2 = client.responses.create(
            model=model,
            temperature=0.1,
            max_output_tokens=1500,
            instructions="Return ONLY the JSON object for keys subject, text, html. Nothing else.",
            input=[{"role": "user", "content": "Finalize JSON now."}],
            tools=[{"type": "web_search"}],
            tool_choice="none",
            text={
                "format": {
                    "type": "json_schema",
                    "name": "newsletter_payload",
                    "schema": schema,
                    "strict": True,
                }
            },
        )
        raw_text2 = resp2.output_text or ""
        logging.info("[generate] retry output_text length=%d", len(raw_text2))
        payload = json.loads(raw_text2)
        resp = resp2  # keep the finalized response for annotation harvesting

    # Validate shape
    NewsletterPayload.model_validate(payload)

    # 1) Prefer annotation-based sources
    sources_list = _extract_sources_from_resp(resp)

    # 2) Fallback: parse URLs from HTML and filter to allowed domains
    if not sources_list:
        html = payload.get("html", "") or ""
        extracted = _extract_urls_from_html(html)
        allowed = _filter_allowed(extracted, sources_param)
        sources_list = [{"title": "", "url": u, "source": ""} for u in allowed]

    # 3) Hard fail if still empty
    if not sources_list:
        logging.error("[generate] No sources captured from annotations or HTML fallback.")
        raise RuntimeError(
            "No sources captured from annotations or HTML. Check allowed domains, web_search availability, and instructions."
        )

    payload["sources"] = sources_list
    return payload

# -----------------------------------------------------------------------------
# Email sender
# -----------------------------------------------------------------------------
def _coerce_recipients(r) -> List[str]:
    if not r:
        r = os.getenv("EMAIL_RECIPIENTS", "")
    if isinstance(r, list):
        return r
    return [x.strip() for x in str(r).replace(";", ",").split(",") if x.strip()]

def send_email(subject: str, text_body: str, html_body: str, recipients=None, sources=None):
    """
    Sends the email. If 'sources' are present, appends a Sources section to HTML.
    """
    to_list = _coerce_recipients(recipients)
    if not to_list:
        raise ValueError("No recipients provided")

    if sources:
        lis = "".join(
            [f'<li><a href="{s.get("url","#")}">{s.get("title","Source") or s.get("url","#")}</a></li>' for s in sources[:20]]
        )
        html_body = f'{html_body}<hr><p><strong>Sources</strong></p><ul>{lis}</ul>'

    msg = EmailMessage()
    msg["Subject"] = subject or "(no subject)"
    msg["From"] = os.getenv("EMAIL_FROM")
    msg["To"] = ", ".join(to_list)
    msg.set_content(text_body or " ")
    # ensure HTML exists even if model returns empty
    msg.add_alternative(html_body or markdown(text_body or ""), subtype="html")

    smtp_host = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USERNAME")
    smtp_pass = os.getenv("SMTP_PASSWORD")

    logging.info("[email] sending to=%s via %s:%s as %s", to_list, smtp_host, smtp_port, smtp_user)

    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)

    logging.info("[email] sent OK")

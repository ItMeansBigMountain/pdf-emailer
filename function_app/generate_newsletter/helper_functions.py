# helper_functions.py (final, with structured sources + robust parsing + debug logs)
import os
import json
import logging
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, ValidationError

# Basic logger config (Functions picks this up)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("newsletter")

SYSTEM_INSTRUCTIONS = (
    "You are a senior newsletter editor.\n"
    "You have the web_search tool enabled. Only use it to fetch RECENT articles "
    "from the allowed domains. Prefer last 7–14 days. Include the exact URL in annotations.\n"
    "Return ONLY JSON matching the schema. Do NOT include markdown fences. Do NOT include prose."
)

# ---------- Pydantic models for validation ----------

class SourceItem(BaseModel):
    title: str = Field(..., description="Short article/source title")
    url: str   = Field(..., description="Canonical URL to the article")
    source: str | None = Field(default=None, description="Optional source/domain")

class NewsletterPayload(BaseModel):
    subject: str = Field(..., max_length=78, description="Email subject, <=78 chars.")
    text: str    = Field(..., description="Plaintext body for clients without HTML.")
    html: str    = Field(..., description="Inline-friendly HTML, no external CSS/scripts.")
    sources: List[SourceItem] = Field(
        ..., min_items=1, description="At least 1 recent source (title + url) used in the newsletter."
    )

# ---------- Prompt builders ----------

def _build_user_task(
    audience: str, tone: str, title: str, cta: str, cta_note: str,
    custom_prompt: str, topic: Optional[str], sources: List[str]
) -> str:
    src_lines = "\n".join(f"- {d}" for d in sources)
    topic_line = f"Topic focus: {topic}" if topic else "Topic focus: latest noteworthy items"
    return (
        f"{topic_line}\nAllowed domains only:\n{src_lines}\n\n"
        f"Audience: {audience}\nTone: {tone}\nTitle: {title}\n"
        f"CTA label: {cta}\nCTA note: {cta_note}\nExtra instructions: {custom_prompt}\n"
        "Tasks:\n"
        "1) Use the web_search tool to find the most recent, high-signal articles from ONLY the allowed domains.\n"
        "2) Synthesize a concise newsletter for the audience with the requested tone and CTA.\n"
        "3) Return only the structured object defined by the schema (subject, text, html, sources[]). No extra keys.\n"
        "4) Each item in sources MUST include a usable URL.\n"
        "5) Include citations as annotations so URLs can also appear as metadata."
    )

# ---------- OpenAI client + schema ----------

def _get_openai_client():
    from openai import OpenAI
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY not set")
    return OpenAI()

def _json_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "subject": { "type": "string", "description": "Email subject, <=78 chars." },
            "text":    { "type": "string", "description": "Plaintext body." },
            "html":    { "type": "string", "description": "Inline-safe HTML only." },
            "sources": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "properties": {
                        "title":  { "type": "string" },
                        "url":    { "type": "string" },
                        "source": { "type": ["string", "null"] }
                    },
                    "required": ["title", "url"],
                    "additionalProperties": False
                }
            }
        },
        "required": ["subject", "text", "html", "sources"],
        "additionalProperties": False
    }

# ---------- Utilities ----------

def _extract_sources_from_annotations(resp) -> List[Dict[str, str]]:
    """
    Best effort: read URL annotations from last assistant message and turn them into source dicts.
    """
    items = [it for it in getattr(resp, "output", []) if getattr(it, "type", "") == "message"]
    if not items:
        return []
    last = items[-1]
    extracted: List[Dict[str, str]] = []
    for block in getattr(last, "content", []) or []:
        for ann in getattr(block, "annotations", []) or []:
            if getattr(ann, "type", "") == "url" and getattr(ann, "url", ""):
                extracted.append({
                    "title": getattr(ann, "title", "") or "",
                    "url": ann.url,
                    "source": None
                })
    return extracted

def _dedupe_sources(primary: List[Dict[str, str]], extra: List[Dict[str, str]]) -> List[Dict[str, str]]:
    seen = set()
    merged: List[Dict[str, str]] = []
    for s in (primary + extra):
        url = (s.get("url") or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        merged.append({
            "title": s.get("title") or "",
            "url": url,
            "source": s.get("source")
        })
    return merged

# ---------- Main generation ----------

def generate_newsletter_via_openai_websearch(
    audience: str, tone: str, title: str, cta: str, cta_note: str,
    custom_prompt: str, sources: List[str], topic: Optional[str] = None,
    model: Optional[str] = None, temperature: float = 0.2, max_turns: int = 1
) -> Dict:
    if not sources:
        raise ValueError("Provide at least one domain in `sources`")

    client = _get_openai_client()
    model = model or os.getenv("LLM_MODEL", "gpt-4o-2024-08-06")
    schema = _json_schema()
    user_input = _build_user_task(audience, tone, title, cta, cta_note, custom_prompt, topic, sources)

    # First turn: allow web_search and enforce JSON Schema via `text.format`
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
                "strict": True
            }
        }
    )

    # If the first turn produced no output_text (e.g., still in tool call), force a finalize turn
    if not getattr(resp, "output_text", None) and max_turns > 0:
        resp = client.responses.create(
            model=model,
            temperature=min(temperature, 0.1),
            max_output_tokens=1500,
            instructions="Return ONLY the JSON object for keys subject, text, html, sources[]. Nothing else.",
            input=[{"role": "user", "content": "Finalize JSON now."}],
            tools=[{"type": "web_search"}],
            tool_choice="none",
            text={
                "format": {
                    "type": "json_schema",
                    "name": "newsletter_payload",
                    "schema": schema,
                    "strict": True
                }
            }
        )

    # DEBUG: capture exactly what the model returned
    raw = getattr(resp, "output_text", "")
    log.info("LLM output_text (truncated 4k): %s", (raw[:4000] + ("..." if len(raw) > 4000 else "")))

    # Parse JSON strictly; fallback to one more finalize if needed
    try:
        parsed = json.loads(raw)
    except Exception:
        log.warning("Primary JSON parse failed; issuing strict finalize retry.")
        resp2 = client.responses.create(
            model=model,
            temperature=0.1,
            max_output_tokens=1500,
            instructions="Return ONLY the JSON object for keys subject, text, html, sources[]. Nothing else.",
            input=[{"role": "user", "content": "Finalize JSON now."}],
            tools=[{"type": "web_search"}],
            tool_choice="none",
            text={
                "format": {
                    "type": "json_schema",
                    "name": "newsletter_payload",
                    "schema": schema,
                    "strict": True
                }
            }
        )
        raw = getattr(resp2, "output_text", "")
        log.info("LLM finalize output_text (truncated 4k): %s", (raw[:4000] + ("..." if len(raw) > 4000 else "")))
        parsed = json.loads(raw)
        resp = resp2  # keep the last response for annotations too

    # Validate shape
    try:
        payload = NewsletterPayload.model_validate(parsed).model_dump()
    except ValidationError as ve:
        # Log entire invalid payload for diagnosis
        log.error("Structured output failed validation: %s", ve)
        log.error("Invalid payload JSON (truncated 4k): %s", (json.dumps(parsed)[:4000] + "..."))
        raise

    # Merge any URL annotations (if present) with structured sources
    ann_sources = _extract_sources_from_annotations(resp)
    payload["sources"] = _dedupe_sources(payload.get("sources", []), ann_sources)

    # Guarantee at least one source (schema already enforces, but we re-check after merge/dedupe)
    if not payload["sources"]:
        raise RuntimeError("Model returned zero sources after merge. Check domains/model/web_search availability.")

    return payload

# ---------- Email sender (unchanged interface) ----------

import smtplib
from email.message import EmailMessage
from markdown2 import markdown

def _coerce_recipients(r):
    if not r:
        r = os.getenv("EMAIL_RECIPIENTS", "")
    if isinstance(r, list):
        return r
    return [x.strip() for x in str(r).replace(";", ",").split(",") if x.strip()]

def send_email(subject: str, text_body: str, html_body: str, recipients=None, sources=None):
    to_list = _coerce_recipients(recipients)
    if not to_list:
        raise ValueError("No recipients provided")

    # Append sources list to HTML footer (nice UX)
    if sources:
        lis = "".join(
            [f'<li><a href="{s.get("url","#")}">{s.get("title","Source")}</a></li>' for s in sources[:10]]
        )
        html_body = f'{html_body}<hr><p><strong>Sources</strong></p><ul>{lis}</ul>'

    msg = EmailMessage()
    msg["Subject"] = subject or "(no subject)"
    msg["From"] = os.getenv("EMAIL_FROM")
    msg["To"] = ", ".join(to_list)
    msg.set_content(text_body or " ")
    msg.add_alternative(html_body or markdown(text_body or ""), subtype="html")

    with smtplib.SMTP(os.getenv("SMTP_SERVER"), int(os.getenv("SMTP_PORT", "587")), timeout=20) as server:
        server.starttls()
        server.login(os.getenv("SMTP_USERNAME"), os.getenv("SMTP_PASSWORD"))
        server.send_message(msg)

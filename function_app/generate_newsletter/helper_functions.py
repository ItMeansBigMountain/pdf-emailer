# function_app/generate_newsletter/helper_functions.py
import os
import json
import logging
import smtplib
from typing import List, Dict, Optional
from email.message import EmailMessage

from markdown2 import markdown
from pydantic import BaseModel, Field

# Optional verbose logging for debugging model I/O
DEBUG = os.getenv("DEBUG_LOG_MODEL", "0") == "1"
logger = logging.getLogger("newsletter")
if DEBUG:
    logging.getLogger().setLevel(logging.INFO)

SYSTEM_INSTRUCTIONS = (
    "You are a senior newsletter editor.\n"
    "You have the web_search tool enabled. Only use it to fetch RECENT articles "
    "from the allowed domains. Prefer last 7–14 days. Include the exact URL in annotations.\n"
    "Return ONLY JSON matching the schema. Do NOT include markdown fences. Do NOT include prose."
)

class NewsletterPayload(BaseModel):
    subject: str = Field(..., max_length=78, description="Email subject, <=78 chars.")
    text: str   = Field(..., description="Plaintext body for clients without HTML.")
    html: str   = Field(..., description="Inline-friendly HTML, no external CSS/scripts.")

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
        "2) Synthesize a concise newsletter for the audience with the requested tone and CTA.\n"
        "3) Return only the structured object defined by the schema (subject, text, html). No extra keys.\n"
        "4) Include citations as annotations so URLs can be read from the response."
    )

def _get_openai_client():
    from openai import OpenAI
    # Reads OPENAI_API_KEY from environment
    return OpenAI()

def _json_schema():
    return {
        "type": "object",
        "properties": {
            "subject": {"type": "string", "description": "Email subject, <=78 chars."},
            "text":    {"type": "string", "description": "Plaintext body."},
            "html":    {"type": "string", "description": "Inline-safe HTML only."},
        },
        "required": ["subject", "text", "html"],
        "additionalProperties": False,
    }

def _extract_sources_from_resp(resp) -> List[Dict[str, str]]:
    # Harvest URL annotations from the last assistant message (if present)
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

def _log_response(resp, label: str):
    if not DEBUG:
        return
    try:
        logger.info("=== %s: status=%s model=%s ===", label, getattr(resp, "status", None), getattr(resp, "model", None))
        for i, item in enumerate(getattr(resp, "output", []) or []):
            logger.info("output[%d].type=%s role=%s", i, getattr(item, "type", None), getattr(item, "role", None))
            for j, block in enumerate(getattr(item, "content", []) or []):
                t = getattr(block, "type", None)
                if t == "output_text":
                    text = getattr(block, "text", "")
                    logger.info("  content[%d]: output_text (%d chars) preview=%r", j, len(text), text[:300])
                else:
                    logger.info("  content[%d]: %s", j, t)
        logger.info("output_text preview=%r", (getattr(resp, "output_text", "") or "")[:500])
    except Exception as e:
        logger.info("failed to log response: %s", e)

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
    Uses Responses API + Structured Outputs JSON Schema.
    IMPORTANT: web_search tool must be declared as {"type": "web_search"} only.
    """
    if not sources:
        raise ValueError("Provide at least one domain in `sources`")

    client = _get_openai_client()
    model = model or os.getenv("LLM_MODEL", "gpt-4o-2024-08-06")
    schema = _json_schema()
    user_input = _build_user_task(audience, tone, title, cta, cta_note, custom_prompt, topic, sources)

    # Turn 1: allow tool use, require strict JSON via text.format
    resp = client.responses.create(
        model=model,
        temperature=temperature,
        max_output_tokens=1500,
        instructions=SYSTEM_INSTRUCTIONS,
        input=[{"role": "user", "content": user_input}],
        tools=[{"type": "web_search"}],          # <-- no extra fields allowed here
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
    _log_response(resp, "turn1")

    # If tool chatter occurred and no JSON yet, run a finalize pass without tools
    if not getattr(resp, "output_text", None):
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
        _log_response(resp, "finalize")

    # Parse JSON (retry once if needed)
    try:
        payload = json.loads(resp.output_text)
    except Exception:
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
        _log_response(resp2, "retry_finalize")
        payload = json.loads(resp2.output_text)
        resp = resp2

    # Validate shape strictly (helps catch partial JSON and schema drift)
    NewsletterPayload.model_validate(payload)

    # Attach source URLs (from annotations)
    payload["sources"] = _extract_sources_from_resp(resp)
    return payload

# ---------------- Email helper ----------------

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

    # Append a short sources list at the bottom of HTML
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

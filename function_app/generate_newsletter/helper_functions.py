# helper_functions.py (final)

import os, json, smtplib
from typing import List, Dict, Optional
from email.message import EmailMessage

from pydantic import BaseModel, Field
from markdown2 import markdown


SYSTEM_INSTRUCTIONS = (
    "You are a senior newsletter editor.\n"
    "Use the web_search tool to fetch ONLY RECENT articles (<=14 days) from the allowed domains.\n"
    "Prefer high-signal primary sources. Insert inline citations so URLs appear as annotations.\n"
    "Return ONLY JSON matching the schema (subject, text, html). No prose, no code fences."
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
        f"{topic_line}\n"
        f"Time window: last 14 days.\n"
        f"Allowed domains ONLY:\n{src_lines}\n\n"
        f"Audience: {audience}\nTone: {tone}\nTitle: {title}\n"
        f"CTA label: {cta}\nCTA note: {cta_note}\nExtra instructions: {custom_prompt}\n"
        "Tasks:\n"
        "1) Use web_search to find the most recent, high-signal items from ONLY the allowed domains.\n"
        "2) Synthesize a concise newsletter for this audience and tone; insert inline citations after claims.\n"
        "3) Output only the strict JSON object {subject, text, html}. No other keys."
    )


def _get_openai_client():
    from openai import OpenAI
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY not set")
    return OpenAI()


def _json_schema():
    # Strict JSON schema for Structured Outputs
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
    """Harvest URL annotations (if the model cited inline)."""
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
    Generates a newsletter by forcing web search + structured outputs.
    Returns dict with subject, text, html, and sources (from URL annotations).
    """
    if not sources:
        raise ValueError("Provide at least one domain in `sources`")

    from json import loads

    client = _get_openai_client()
    model = model or os.getenv("LLM_MODEL", "gpt-4o-2024-08-06")
    schema = _json_schema()
    user_input = _build_user_task(audience, tone, title, cta, cta_note, custom_prompt, topic, sources)

    # Turn 1: allow web_search; enforce strict JSON via text.format json_schema
    resp = client.responses.create(
        model=model,
        temperature=temperature,
        max_output_tokens=1500,
        instructions=SYSTEM_INSTRUCTIONS,
        input=[{"role": "user", "content": user_input}],
        tools=[{"type": "web_search", "recency_days": 14}],
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

    # Detect whether any search actually happened
    used_search = any(getattr(it, "type", "") == "web_search_call" for it in getattr(resp, "output", []))

    # If no JSON (tool chatter) or no search happened, finalize in a second turn with no further tools
    if not getattr(resp, "output_text", None) or not used_search or max_turns > 1:
        resp = client.responses.create(
            model=model,
            temperature=min(temperature, 0.1),
            max_output_tokens=1500,
            instructions="Return ONLY the JSON object for keys subject, text, html. Nothing else.",
            input=[{"role": "user", "content": "Finalize JSON now. JSON only."}],
            tools=[{"type": "web_search", "recency_days": 14}],
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

    if not getattr(resp, "output_text", None):
        raise RuntimeError("Model did not produce JSON output_text; cannot proceed.")

    # Parse JSON. If it fails, do one last belt-and-suspenders finalize.
    try:
        payload = loads(resp.output_text)
    except Exception:
        resp2 = client.responses.create(
            model=model,
            temperature=0.1,
            max_output_tokens=1500,
            instructions="Return ONLY the JSON object for keys subject, text, html. Nothing else.",
            input=[{"role": "user", "content": "Finalize JSON now. JSON only."}],
            tools=[{"type": "web_search", "recency_days": 14}],
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
        if not getattr(resp2, "output_text", None):
            raise RuntimeError("Model did not produce JSON on retry; aborting.")
        payload = loads(resp2.output_text)
        resp = resp2  # keep for annotation harvesting

    # Validate contract
    NewsletterPayload.model_validate(payload)

    # Attach sources from annotations
    payload["sources"] = _extract_sources_from_resp(resp)
    return payload


# ---------------- Email helpers ----------------

def _coerce_recipients(r):
    if not r:
        r = os.getenv("EMAIL_RECIPIENTS", "")
    if isinstance(r, list):
        return r
    return [x.strip() for x in str(r).replace(";", ",").split(",") if x.strip()]


def send_email(subject: str, text_body: str, html_body: str, recipients=None, sources=None):
    """
    Sends an email with both text and HTML parts.
    Appends a Sources list (if provided) to the HTML.
    """
    to_list = _coerce_recipients(recipients)
    if not to_list:
        raise ValueError("No recipients provided")

    # Append sources (first 10) to HTML, if any
    if sources:
        lis = "".join(
            [f'<li><a href="{s.get("url", "#")}">{(s.get("title") or "Source").strip() or "Source"}</a></li>'
             for s in sources[:10]]
        )
        html_body = f'{html_body}<hr><p><strong>Sources</strong></p><ul>{lis}</ul>'

    msg = EmailMessage()
    msg["Subject"] = subject or "(no subject)"
    msg["From"] = os.getenv("EMAIL_FROM")
    msg["To"] = ", ".join(to_list)

    # Text + HTML
    msg.set_content(text_body or " ")
    msg.add_alternative(html_body or markdown(text_body or ""), subtype="html")

    with smtplib.SMTP(os.getenv("SMTP_SERVER"), int(os.getenv("SMTP_PORT", "587")), timeout=20) as server:
        server.starttls()
        server.login(os.getenv("SMTP_USERNAME"), os.getenv("SMTP_PASSWORD"))
        server.send_message(msg)

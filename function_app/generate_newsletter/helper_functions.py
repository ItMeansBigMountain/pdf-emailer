# function_app/generate_newsletter/helper_functions.py

import os, json, re, smtplib
from typing import List, Dict, Optional, Tuple
from email.message import EmailMessage
from dotenv import load_dotenv
from markdown2 import markdown
from openai import OpenAI

load_dotenv()

SYSTEM_INSTRUCTIONS = (
    "You are a senior newsletter editor.\n"
    "You have the web_search tool enabled. Use it to fetch RECENT articles "
    "from ONLY the allowed domains, prioritizing the last 7–14 days.\n"
    "Return ONLY a JSON object with keys: subject, text, html. No prose outside JSON.\n"
    "Subject <= 78 chars. html must be inline-friendly, no external CSS/scripts."
)

NEWSLETTER_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "subject": {
            "type": "string",
            "description": "Email subject, <=78 chars."
        },
        "text": {
            "type": "string",
            "description": "Plaintext body for clients without HTML."
        },
        "html": {
            "type": "string",
            "description": "Inline-friendly HTML body."
        }
    },
    "required": ["subject", "text", "html"],
    "additionalProperties": False
}

def _get_openai_client() -> OpenAI:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY not set")
    return OpenAI(api_key=key)

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
        "1) Use web_search NOW to find the 3–6 most recent, high-signal articles from ONLY the allowed domains.\n"
        "2) Aggregate into a concise newsletter. Include 2 short bullets of key takeaways.\n"
        "3) Return ONLY JSON {\"subject\":\"...\",\"text\":\"...\",\"html\":\"...\"}.\n"
        "4) Place source URLs as citations in content so they appear as annotations."
    )

def _extract_sources_from_resp(resp) -> List[Dict[str, str]]:
    # Scrape URL annotations from the last assistant message
    try:
        msgs = [it for it in getattr(resp, "output", []) if getattr(it, "type", None) == "message"]
        if not msgs:
            return []
        last = msgs[-1]
        out: List[Dict[str, str]] = []
        for block in getattr(last, "content", []) or []:
            for ann in getattr(block, "annotations", []) or []:
                if getattr(ann, "type", "") == "url" and getattr(ann, "url", ""):
                    out.append({"title": getattr(ann, "title", "") or "", "url": ann.url, "source": ""})
        return out
    except Exception:
        return []

def _first_json_object(s: str) -> Optional[str]:
    # Pull the first top-level JSON object {...} to salvage minor drift
    m = re.search(r"\{(?:[^{}]|(?R))*\}", s, re.DOTALL)
    return m.group(0) if m else None

def _safe_parse_newsletter(text: str) -> Dict[str, str]:
    try:
        return json.loads(text)
    except Exception:
        blob = _first_json_object(text or "")
        if blob:
            return json.loads(blob)
        raise

def generate_newsletter_via_openai_websearch(
    audience: str, tone: str, title: str, cta: str, cta_note: str,
    custom_prompt: str, sources: List[str], topic: Optional[str] = None,
    model: Optional[str] = None, temperature: float = 0.2, max_turns: int = 2
) -> Dict:
    if not sources:
        raise ValueError("Provide at least one domain in `sources`")

    client = _get_openai_client()
    user_input = _build_user_task(audience, tone, title, cta, cta_note, custom_prompt, topic, sources)
    # Use a structured-outputs-capable snapshot
    model = model or os.getenv("LLM_MODEL", "gpt-4o-2024-08-06")

    # Turn 1: allow web_search, enforce strict JSON Schema
    resp1 = client.responses.create(
        model=model,
        temperature=temperature,
        instructions=SYSTEM_INSTRUCTIONS,
        input=[{"role": "user", "content": user_input}],
        tools=[{"type": "web_search"}],
        tool_choice="auto",
        max_output_tokens=900,
        text={
            "format": {
                "type": "json_schema",
                "name": "newsletter_payload",
                "schema": NEWSLETTER_JSON_SCHEMA,
                "strict": True,
            }
        },
    )

    # If you want a second turn to finalize without tools:
    resp_final = resp1
    if max_turns > 1:
        resp2 = client.responses.create(
            model=model,
            temperature=min(temperature, 0.15),
            instructions=SYSTEM_INSTRUCTIONS,
            input=[{"role": "user", "content": "Finalize. Return ONLY the JSON object."}],
            tools=[{"type": "web_search"}],
            tool_choice="none",
            max_output_tokens=900,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "newsletter_payload",
                    "schema": NEWSLETTER_JSON_SCHEMA,
                    "strict": True,
                }
            },
        )
        resp_final = resp2

    # Parse strictly; if the SDK gives you the string, use output_text
    raw_text = getattr(resp_final, "output_text", "") or ""
    if not raw_text:
        # Some SDK builds nest the text in content; backstop:
        try:
            item = resp_final.output[0].content[0]
            raw_text = getattr(item, "text", "")
        except Exception:
            raw_text = ""

    data = _safe_parse_newsletter(raw_text)
    for k in ("subject", "text", "html"):
        if not isinstance(data.get(k), str):
            raise ValueError(f"Model returned non-string for {k}")

    # Use the FIRST turn’s annotations (that’s where web_search usually attached)
    sources_list = _extract_sources_from_resp(resp1) or _extract_sources_from_resp(resp_final)
    data["sources"] = sources_list
    return data

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

    if sources:
        lis = "".join([f'<li><a href="{s.get("url","#")}">{s.get("title","Source")}</a></li>' for s in sources[:10]])
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

# function_app/generate_newsletter/helper_functions.py  (patched core)

import os, logging, smtplib
from typing import List, Dict, Optional
from email.message import EmailMessage
from markdown2 import markdown
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()

SYSTEM_INSTRUCTIONS = (
    "You are a senior newsletter editor.\n"
    "Use the web_search tool to fetch RECENT items (last 7–14 days) ONLY from allowed domains.\n"
    "Do not invent sources. Prefer original reporting. Include 3–6 concrete items with names, dates, and links.\n"
    "Return ONLY the structured model. No extra text.\n"
)

class NewsletterPayload(BaseModel):
    subject: str = Field(..., max_length=78, description="Email subject, <=78 chars.")
    text: str   = Field(..., description="Plaintext body for clients without HTML.")
    html: str   = Field(..., description="Inline-friendly HTML, no external CSS/scripts.")

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
        "Requirements:\n"
        "- Use the web_search tool now. Do not summarize without checking sources.\n"
        "- Pull 3–6 recent items, each with outlet, date, 1–2 sentence summary.\n"
        "- Include inline links; citations should appear as annotations.\n"
        "- No generic filler. No placeholders.\n"
        "Return only the structured object."
    )

def _extract_sources_from_resp(resp) -> List[Dict[str, str]]:
    # Pull URL annotations from the assistant message
    items = [it for it in getattr(resp, "output", []) if getattr(it, "type", None) == "message"]
    if not items:
        return []
    last_msg = items[-1]
    out: List[Dict[str, str]] = []
    for block in getattr(last_msg, "content", []) or []:
        for ann in getattr(block, "annotations", []) or []:
            if getattr(ann, "type", "") == "url" and getattr(ann, "url", ""):
                out.append({
                    "title": getattr(ann, "title", "") or "",
                    "url": ann.url,
                    "source": ""
                })
    return out

def generate_newsletter_via_openai_websearch(
    audience: str, tone: str, title: str, cta: str, cta_note: str,
    custom_prompt: str, sources: List[str], topic: Optional[str] = None,
    model: Optional[str] = None, temperature: float = 0.3, max_turns: int = 1  # ignored; single-call by design
) -> Dict:
    if not sources:
        raise ValueError("Provide at least one domain in `sources`")

    user_input = _build_user_task(audience, tone, title, cta, cta_note, custom_prompt, topic, sources)
    model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")

    # Single call: web_search enabled; structured outputs enforced
    resp = client.responses.parse(
        model=model,
        temperature=temperature,
        instructions=SYSTEM_INSTRUCTIONS,
        input=[{"role": "user", "content": user_input}],
        tools=[{"type": "web_search"}],
        tool_choice="auto",
        text_format=NewsletterPayload,
        max_output_tokens=1200,
    )

    payload: NewsletterPayload = resp.output_parsed
    srcs = _extract_sources_from_resp(resp)

    # Fail loud if we didn’t actually cite anything
    if not srcs:
        logging.error("No sources extracted from annotations. Returning diagnostic body.")
        raise RuntimeError("No sources found. Ensure model is allowed to use web_search and domains are reachable.")

    result = payload.model_dump()
    result["sources"] = srcs
    return result


# Email helpers unchanged
def _coerce_recipients(r):
    if not r:
        r = os.getenv("EMAIL_RECIPIENTS", "")
    if isinstance(r, list):
        return r
    return [x.strip() for x in str(r).replace(";", ",").split(",") if x.strip()]

def send_email(subject: str, text_body: str, html_body: str, recipients=None, sources=None):
    import ssl
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

    context = ssl.create_default_context()
    with smtplib.SMTP(os.getenv("SMTP_SERVER"), int(os.getenv("SMTP_PORT", "587")), timeout=20) as server:
        server.starttls(context=context)
        server.login(os.getenv("SMTP_USERNAME"), os.getenv("SMTP_PASSWORD"))
        server.send_message(msg)

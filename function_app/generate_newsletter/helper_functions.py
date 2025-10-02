import os, json, smtplib
from typing import List, Dict, Optional, Tuple
from email.message import EmailMessage
from dotenv import load_dotenv
from markdown2 import markdown
from pydantic import BaseModel, Field

load_dotenv()

SYSTEM_INSTRUCTIONS = (
    "You are a senior newsletter editor.\n"
    "You have the web_search tool enabled. You MUST call it at least once to fetch RECENT articles "
    "from ONLY the allowed domains. Prefer the last 7–14 days. "
    "Include exact source URLs in either message annotations or the search results you cite.\n"
    "Return a structured object that matches the provided model exactly."
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
        f"CTA label: {cta}\nCTA note: {cta_note}\nExtra instructions: {custom_prompt}\n\n"
        "Output requirements:\n"
        "- Use web_search with recency 14 days and restrict to the allowed domains.\n"
        "- Synthesize a concise newsletter with this outline:\n"
        "  1) Top 3 Headlines (1–2 lines each, include source)\n"
        "  2) Market Moves (50–80 words)\n"
        "  3) Quick Hits (3 bullets, 1 line each)\n"
        "- Include the CTA at the bottom.\n"
        "- Return ONLY the structured object with keys subject, text, html.\n"
    )

def _get_openai_client():
    from openai import OpenAI
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY not set")
    return OpenAI(api_key=key)

def _extract_sources_from_annotations(resp) -> List[Dict[str, str]]:
    sources: List[Dict[str, str]] = []
    msg_items = [it for it in getattr(resp, "output", []) if getattr(it, "type", None) == "message"]
    if not msg_items:
        return sources
    last_msg = msg_items[-1]
    for block in getattr(last_msg, "content", []) or []:
        anns = getattr(block, "annotations", []) or []
        for ann in anns:
            if getattr(ann, "type", "") == "url" and getattr(ann, "url", ""):
                sources.append({
                    "title": getattr(ann, "title", "") or "",
                    "url": ann.url,
                    "source": ""
                })
    return sources

def _extract_sources_from_search_results(resp) -> List[Dict[str, str]]:
    # Fallback: collect from web_search_results output blocks
    results: List[Dict[str, str]] = []
    for item in getattr(resp, "output", []):
        if getattr(item, "type", "") == "web_search_results":
            for r in getattr(item, "results", []) or []:
                url = getattr(r, "url", "") or r.get("url") if isinstance(r, dict) else ""
                title = getattr(r, "title", "") or r.get("title") if isinstance(r, dict) else ""
                if url:
                    results.append({"title": title or "", "url": url, "source": ""})
    return results

def _has_search_call(resp) -> bool:
    return any(getattr(it, "type", "") == "web_search_call" for it in getattr(resp, "output", []))

def _merge_sources(a: List[Dict[str, str]], b: List[Dict[str, str]]) -> List[Dict[str, str]]:
    seen = set()
    out = []
    for s in (a + b):
        key = s.get("url", "")
        if key and key not in seen:
            seen.add(key)
            out.append(s)
    return out

def generate_newsletter_via_openai_websearch(
    audience: str, tone: str, title: str, cta: str, cta_note: str,
    custom_prompt: str, sources: List[str], topic: Optional[str] = None,
    model: Optional[str] = None, temperature: float = 0.3, max_turns: int = 2
) -> Dict:
    if not sources:
        raise ValueError("Provide at least one domain in `sources`")

    client = _get_openai_client()
    user_input = _build_user_task(audience, tone, title, cta, cta_note, custom_prompt, topic, sources)
    model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")

    # Turn 1: ask, allow tools
    resp1 = client.responses.parse(
        model=model,
        temperature=temperature,
        instructions=SYSTEM_INSTRUCTIONS,
        input=[{"role": "user", "content": user_input}],
        tools=[{"type": "web_search"}],
        tool_choice="auto",
        max_output_tokens=1200,
        text_format=NewsletterPayload,
    )
    payload = resp1.output_parsed

    used_search = _has_search_call(resp1)
    sources_1 = _merge_sources(
        _extract_sources_from_annotations(resp1),
        _extract_sources_from_search_results(resp1)
    )

    # Turn 2: if no search happened or we found zero sources, force it
    resp_final = resp1
    if max_turns > 1 and (not used_search or len(sources_1) == 0):
        force_msg = (
            "You did not perform web_search. Now call web_search with recency_days=14 and queries "
            f"restricted to these domains: {', '.join(sources)}. Use the topic as keywords. "
            "Then synthesize and return ONLY the structured object."
        )
        resp2 = client.responses.parse(
            model=model,
            temperature=min(temperature, 0.2),
            instructions=SYSTEM_INSTRUCTIONS,
            input=[{"role": "user", "content": force_msg}],
            tools=[{"type": "web_search"}],
            tool_choice="auto",
            max_output_tokens=1200,
            text_format=NewsletterPayload,
        )
        payload = resp2.output_parsed
        resp_final = resp2
        sources_2 = _merge_sources(
            _extract_sources_from_annotations(resp2),
            _extract_sources_from_search_results(resp2)
        )
        sources_1 = _merge_sources(sources_1, sources_2)

    result = payload.model_dump()
    result["sources"] = sources_1
    return result

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

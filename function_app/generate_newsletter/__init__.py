# function_app/generate_newsletter/__init__.py

import json
import azure.functions as func
from .helper_functions import generate_newsletter_via_openai_websearch, send_email

def main(req: func.HttpRequest) -> func.HttpResponse:
    d = req.get_json() or {}

    payload = generate_newsletter_via_openai_websearch(
        audience=d.get("audience", "operators"),
        tone=d.get("tone", "concise"),
        title=d.get("title", "Weekly Brief"),
        cta=d.get("cta", "Read more"),
        cta_note=d.get("cta_note", "3-minute skim"),
        custom_prompt=d.get("custom_prompt", ""),
        sources=d.get("sources", ["reuters.com", "theverge.com", "ft.com"]),
        topic=d.get("topic"),
        model=d.get("model", "gpt-4o-2024-08-06"),
        temperature=float(d.get("temperature", 0.2)),
        max_turns=int(d.get("max_turns", 2)),
    )

    # optionally email
    if d.get("send_email", True):
        send_email(payload["subject"], payload["text"], payload["html"], recipients=d.get("recipients"), sources=payload.get("sources"))

    body = {
        "status": "ok",
        "subject": payload["subject"],
        "text": payload["text"],
        "html": payload["html"],
        "sources_count": len(payload.get("sources", [])),
        "sources": payload.get("sources", []),
    }
    return func.HttpResponse(json.dumps(body), status_code=200, mimetype="application/json")

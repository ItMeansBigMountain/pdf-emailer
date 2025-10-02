import azure.functions as func
import json
from .helper_functions import generate_newsletter_via_openai_websearch, send_email

def main(req: func.HttpRequest) -> func.HttpResponse:
    d = req.get_json() or {}

    allow_web = bool(d.get("allow_web", True))
    sources = d.get("sources", []) or []
    topic = d.get("topic", None)

    payload = generate_newsletter_via_openai_websearch(
        audience=d.get("audience", "operators"),
        tone=d.get("tone", "concise"),
        title=d.get("title", "Weekly Update"),
        cta=d.get("cta", "Read more"),
        cta_note=d.get("cta_note", "3-minute skim"),
        custom_prompt=d.get("custom_prompt", ""),
        sources=sources,
        topic=topic,
        model=d.get("model", "gpt-4o-mini"),
        temperature=float(d.get("temperature", 0.3)),
        max_turns=int(d.get("max_turns", 2)),
    )

    # email it
    send_email(payload["subject"], payload["text"], payload["html"], recipients=d.get("recipients"), sources=payload.get("sources", []))

    body = {
        "status": "ok",
        "subject": payload["subject"],
        "text": payload["text"],
        "html": payload["html"],
        "sources_count": len(payload.get("sources", [])),
        "sources": payload.get("sources", []),
    }
    return func.HttpResponse(json.dumps(body), status_code=200, mimetype="application/json")

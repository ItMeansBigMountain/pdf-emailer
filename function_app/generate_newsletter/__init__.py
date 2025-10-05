# function_app/generate_newsletter/__init__.py

import json
import logging
import azure.functions as func
from .helper_functions import generate_newsletter_via_openai_websearch, send_email

# Azure Functions already configures logging; keep it simple
logger = logging.getLogger(__name__)

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        d = req.get_json()
    except Exception:
        d = {}

    try:
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

        # Log what the model produced (lengths only, to avoid dumping large HTML)
        logger.info(
            "[result] subject='%s' text_len=%d html_len=%d sources=%d",
            payload.get("subject", "")[:120],
            len(payload.get("text", "") or ""),
            len(payload.get("html", "") or ""),
            len(payload.get("sources", []) or []),
        )

        # email by default (you said you're testing email flows)
        if d.get("send_email", True):
            send_email(
                payload["subject"],
                payload["text"],
                payload["html"],
                recipients=d.get("recipients"),
                sources=payload.get("sources"),
            )

        body = {
            "status": "ok",
            "subject": payload["subject"],
            "text": payload["text"],
            "html": payload["html"],
            "sources_count": len(payload.get("sources", [])),
            "sources": payload.get("sources", []),
        }
        return func.HttpResponse(json.dumps(body), status_code=200, mimetype="application/json")

    except Exception as e:
        logger.exception("Generation failed")
        body = {"status": "error", "stage": "generation", "message": str(e)}
        return func.HttpResponse(json.dumps(body), status_code=500, mimetype="application/json")

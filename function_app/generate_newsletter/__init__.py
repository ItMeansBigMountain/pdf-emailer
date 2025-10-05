# function_app/generate_newsletter/__init__.py

import json
import logging
import azure.functions as func
from .helper_functions import generate_newsletter_via_openai_websearch, send_email

logger = logging.getLogger("newsletter_function")

def _json_response(payload: dict, status: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(payload, ensure_ascii=False),
        status_code=status,
        mimetype="application/json",
    )

def main(req: func.HttpRequest) -> func.HttpResponse:
    # Parse request JSON (Azure Functions Python does not support silent=)
    try:
        d = req.get_json()
        if not isinstance(d, dict):
            d = {}
    except Exception:
        d = {}

    # --- Generate newsletter ---
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
    except Exception as e:
        # Surface a helpful error body for CI/logs
        logger.exception("Generation failed")
        return _json_response(
            {
                "status": "error",
                "stage": "generation",
                "message": str(e),
                "hint": "Set DEBUG_LOG_MODEL=1 to see detailed model/tool traces in logs.",
            },
            status=500,
        )

    # --- Optionally send email ---
    email_status = "skipped"
    email_error = None
    try:
        if d.get("send_email", True):
            send_email(
                payload["subject"],
                payload["text"],
                payload["html"],
                recipients=d.get("recipients"),
                sources=payload.get("sources"),
            )
            email_status = "sent"
    except Exception as e:
        email_status = "error"
        email_error = str(e)
        logger.exception("Email send failed")

    # --- Success response (always returns generated content) ---
    body = {
        "status": "ok",
        "email_status": email_status,
        "email_error": email_error,
        "subject": payload["subject"],
        "text": payload["text"],
        "html": payload["html"],
        "sources_count": len(payload.get("sources", [])),
        "sources": payload.get("sources", []),
    }
    return _json_response(body, status=200)

# function_app/generate_newsletter/__init__.py

import json
import azure.functions as func
from .helper_functions import generate_newsletter_via_openai_websearch, send_email


def _json_response(data: dict, status: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(data),
        status_code=status,
        mimetype="application/json",
    )


def main(req: func.HttpRequest) -> func.HttpResponse:
    # --- Parse request JSON safely ---
    try:
        d = req.get_json()
        if not isinstance(d, dict):
            raise ValueError("JSON body must be an object")
    except Exception:
        d = {}

    # --- Call generator (always uses web search in helper) ---
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
        # generation failure -> 500 with short reason
        return _json_response(
            {
                "status": "error",
                "stage": "generation",
                "message": str(e),
            },
            status=500,
        )

    # --- Optionally email the result ---
    try:
        if d.get("send_email", True):
            send_email(
                payload["subject"],
                payload["text"],
                payload["html"],
                recipients=d.get("recipients"),
                sources=payload.get("sources"),
            )
            emailed = True
        else:
            emailed = False
    except Exception as e:
        # email failure -> 502 but still return the generated content
        return _json_response(
            {
                "status": "error",
                "stage": "email",
                "message": str(e),
                "subject": payload.get("subject"),
                "text": payload.get("text"),
                "html": payload.get("html"),
                "sources_count": len(payload.get("sources", [])),
                "sources": payload.get("sources", []),
            },
            status=502,
        )

    # --- Success ---
    return _json_response(
        {
            "status": "ok",
            "emailed": emailed,
            "subject": payload["subject"],
            "text": payload["text"],
            "html": payload["html"],
            "sources_count": len(payload.get("sources", [])),
            "sources": payload.get("sources", []),
        },
        status=200,
    )

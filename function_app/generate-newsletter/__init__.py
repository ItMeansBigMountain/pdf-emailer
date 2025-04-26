import os
import azure.functions as func
import traceback
import logging
from .helper_functions import initialize_llm, newsletter_prompt, send_email, extract_subject_body

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        data = req.get_json()
        provider = data.get("provider", "openai")
        model = data.get("model", "gpt-3.5-turbo")
        title = data.get("title", "Your Monthly Newsletter")
        temperature = float(data.get("temperature", 0.7))
        audience = data.get("audience", "a general audience")
        stats = data.get("stats", "")
        tone = data.get("tone", "informative")
        cta = data.get("cta", "Learn more on our website!")
        cta_note = data.get("cta_note", "Follow us for updates")
        custom_prompt = data.get("custom_prompt", "Generate a newsletter")
        recipients = data.get("recipients", os.getenv("EMAIL_RECIPIENTS"))

        filled_prompt = newsletter_prompt.format(
            audience=audience,
            stat=stats,
            tone=tone,
            cta=cta,
            cta_note=cta_note,
            title=title,
            custom_prompt=custom_prompt
        )

        llm = initialize_llm(
            provider=provider,
            model_name=model,
            temperature=temperature
        )
        raw_output = llm.invoke(filled_prompt).content
        subject, body = extract_subject_body(raw_output)
        send_email(subject, body, recipients=recipients)

        return func.HttpResponse(
            body=f"Newsletter sent successfully!\n\nSubject: {subject}\nBody : {body}\nRecipients: {recipients}",
            status_code=200
        )

    except Exception as e:
        logging.error("Unhandled exception:\n%s", traceback.format_exc())
        return func.HttpResponse(body=f"Internal Server Error\n\n{traceback.format_exc()}", status_code=500)
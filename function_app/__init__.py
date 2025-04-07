import os
import azure.functions as func
from datetime import datetime
from utils import initialize_llm, generate_pdf, newsletter_prompt, send_email, extract_subject_body

app = func.FunctionApp()

@app.function_name(name="GenerateNewsletterPDF")
@app.route(route="generate-newsletter", auth_level=func.AuthLevel.FUNCTION, methods=["POST"])
def generate_newsletter(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Parse request data
        data = req.get_json()
        audience = data.get("audience", "a general audience")
        stats = data.get("stats", "")
        provider = data.get("provider", "openai")
        model = data.get("model", "gpt-3.5-turbo")
        temperature = float(data.get("temperature", 0.7))
        tone = data.get("tone", "informative")
        cta = data.get("cta", "Learn more on our website!")
        cta_note = data.get("cta_note", "Follow us for updates")
        title = data.get("title", "Your Monthly Newsletter")

        # Fill the prompt template
        filled_prompt = newsletter_prompt.format(
            audience=audience,
            stat=stats,
            tone=tone,
            cta=cta,
            cta_note=cta_note,
            title=title
        )

        # Initialize LLM and generate content
        llm = initialize_llm(provider=provider, model_name=model, temperature=temperature)
        raw_output = llm.invoke(filled_prompt).content

        # Extract subject and body from the LLM output
        subject, body = extract_subject_body(raw_output)

        # Generate PDF
        pdf_stream = generate_pdf(subject, body)

        # Send Email
        send_email(subject, body, pdf_stream)

        # Return the generated PDF as a response
        filename = f"newsletter-{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        return func.HttpResponse(
            body=pdf_stream.read(),
            headers={
                "Content-Type": "application/pdf",
                "Content-Disposition": f'attachment; filename="{filename}"'
            },
            status_code=200
        )

    except Exception as e:
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
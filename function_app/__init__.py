import os
import azure.functions as func
from datetime import datetime
from langchain.chains import LLMChain
from utils import initialize_llm, generate_pdf, prompt_template, send_email

app = func.FunctionApp()

@app.function_name(name="GenerateNewsletterPDF")
@app.route(route="generate-newsletter", auth_level=func.AuthLevel.FUNCTION, methods=["POST"])
def generate_newsletter(req: func.HttpRequest) -> func.HttpResponse:
    try:
        data = req.get_json()
        audience = data.get("audience", "a general audience")
        stats = data.get("stats", "")
        provider = data.get("provider", "openai")
        model = data.get("model", None)
        temperature = float(data.get("temperature", 0.7))

        llm = initialize_llm(provider=provider, model_name=model, temperature=temperature)
        chain = prompt_template | llm
        raw_output = chain.invoke({"audience": audience, "stats": stats})

        if "Subject:" in raw_output and "Body:" in raw_output:
            subject = raw_output.split("Subject:")[1].split("Body:")[0].strip()
            body = raw_output.split("Body:")[1].strip()
        else:
            subject, body = "Newsletter Template", raw_output.strip()

        # Generate PDF
        pdf_stream = generate_pdf(subject, body)

        # Send Email
        send_email(subject, body, pdf_stream)

        # Return file
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

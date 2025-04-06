import os
import logging
import openai
from fpdf import FPDF
from azure.storage.blob import BlobServiceClient
import smtplib
from email.message import EmailMessage
import azure.functions as func
from datetime import datetime

# Load ENV
openai.api_key = os.getenv("LLM_API_KEY")

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_RECIPIENTS = os.getenv("EMAIL_RECIPIENTS").split(",")
STORAGE_CONN_STR = os.getenv("AzureWebJobsStorage")

def generate_pdf(content: str, filename: str) -> str:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, content)

    output_path = f"/tmp/{filename}"
    pdf.output(output_path)
    return output_path

def upload_pdf_to_blob(file_path: str, filename: str):
    blob_service = BlobServiceClient.from_connection_string(STORAGE_CONN_STR)
    container_client = blob_service.get_container_client("generated-pdfs")
    with open(file_path, "rb") as data:
        container_client.upload_blob(name=filename, data=data, overwrite=True)

def send_email_with_attachment(subject: str, body: str, attachment_path: str, attachment_name: str):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = ", ".join(EMAIL_RECIPIENTS)
    msg.set_content(body)

    with open(attachment_path, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename=attachment_name)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)

def get_llm_output() -> str:
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You're a helpful assistant that creates daily PDF reports."},
                {"role": "user", "content": "Generate today's daily summary in 200 words."}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"OpenAI API failed: {e}")
        return "LLM unavailable. Here's a basic fallback report."

def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.utcnow().isoformat()
    logging.info(f"Function ran at {utc_timestamp}")

    content = get_llm_output()
    filename = f"daily-summary-{datetime.now().strftime('%Y-%m-%d')}.pdf"
    pdf_path = generate_pdf(content, filename)

    upload_pdf_to_blob(pdf_path, filename)
    send_email_with_attachment("Daily Summary", content, pdf_path, filename)

    logging.info("PDF generated, uploaded, and emailed.")

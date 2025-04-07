import os
import smtplib
from dotenv import load_dotenv
from io import BytesIO
from datetime import datetime
from fpdf import FPDF
from email.message import EmailMessage
from langchain.prompts import PromptTemplate

# Load .env
load_dotenv()

# --- Prompt ---
# Define a parameterized prompt template for a newsletter/email
newsletter_prompt = PromptTemplate(
    input_variables=["audience", "stat", "tone", "cta", "title", "cta_note"],
    template=(
        "You are a professional copywriter creating a marketing email.\n"
        "Audience: {audience}\n"
        "Tone: {tone}\n"
        "Title/Subject: \"{title}\"\n"
        "Objective: Use the statistic \"{stat}\" to provide value and build credibility.\n"
        "Requirements:\n"
        "- Start with a strong hook that grabs the reader’s attention.\n"
        "- Write in a way that is engaging and not overly salesy or \"cringe\".\n"
        "- Use markdown formatting (headings, bullet points, **bold** text) for readability.\n"
        "- Use 1-2 relevant emojis to add personality (do not overuse them).\n"
        "- Include a clear call-to-action ({cta_note}).\n\n"
        "Now draft the email in Markdown format below.\n"
        "# {title}\n\n"
        "**Hi** {audience},\n\n"
        "_(Hook opening line that piques interest using a relatable scenario or question.)_\n\n"
        "{{Body content focusing on how {stat} relates to the reader's needs, written in a {tone} tone.}}\n\n"
        "- Bullet point highlighting a key benefit or tip\n"
        "- Another key point or insight\n\n"
        "**Call to Action:** {cta}\n\n"
        "*Cheers*,\nYour Company Team"
    )
)

# --- LLM Loader ---
def initialize_llm(provider: str, model_name: str = None, temperature=0.7):
    """Initializes the LLM based on the provider."""
    provider = provider.lower()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    cohere_api_key = os.getenv("COHERE_API_KEY")
    hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model_name or "gpt-3.5-turbo", temperature=temperature, api_key=openai_api_key)
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model_name or "claude-3-7-sonnet-20250219", temperature=temperature, anthropic_api_key=anthropic_api_key)
    elif provider == "cohere":
        from langchain_cohere import ChatCohere
        return ChatCohere(model=model_name or "command", temperature=temperature, cohere_api_key=cohere_api_key)
    elif provider == "huggingface-hub":
        from langchain_community.llms import HuggingFaceHub
        return HuggingFaceHub(repo_id=model_name or "gpt2", huggingfacehub_api_token=hf_token, model_kwargs={"temperature": temperature})
    elif provider == "huggingface-local":
        from langchain_community.llms import HuggingFacePipeline
        from transformers import AutoTokenizer, pipeline, AutoModelForCausalLM
        tokenizer = AutoTokenizer.from_pretrained(model_name or "gpt2")
        model = AutoModelForCausalLM.from_pretrained(model_name or "gpt2")
        pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=500)
        return HuggingFacePipeline(pipeline=pipe)
    else:
        raise Exception(f"Unsupported provider: {provider}")

# --- PDF Generator ---
def generate_pdf(subject, body):
    """Generates a PDF from the given subject and body."""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", 'B', 16)
        pdf.multi_cell(0, 10, subject, align='C')
        pdf.ln(5)
        pdf.set_font("Helvetica", '', 12)
        pdf.multi_cell(0, 10, body)
        buffer = BytesIO()
        pdf.output(buffer)
        buffer.seek(0)
        return buffer
    except Exception as e:
        raise Exception(f"Error generating PDF: {e}")

# --- Email Sender ---
def send_email(subject, body, pdf_bytes):
    """Sends an email with the given subject, body, and PDF attachment."""
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = os.getenv("EMAIL_FROM")
        msg["To"] = os.getenv("EMAIL_RECIPIENTS")
        msg.set_content(body)

        # Attach PDF
        msg.add_attachment(pdf_bytes.read(), maintype="application", subtype="pdf", filename="newsletter.pdf")

        with smtplib.SMTP(os.getenv("SMTP_SERVER"), int(os.getenv("SMTP_PORT", "587"))) as server:
            server.starttls()
            server.login(os.getenv("SMTP_USERNAME"), os.getenv("SMTP_PASSWORD"))
            server.send_message(msg)
    except Exception as e:
        raise Exception(f"Error sending email: {e}")
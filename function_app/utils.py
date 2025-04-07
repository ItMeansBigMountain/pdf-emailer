import os
import azure.functions as func
from fpdf import FPDF
from io import BytesIO
from datetime import datetime

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# LangChain imports
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Init LLM
def initialize_llm(provider: str, model_name: str = None, temperature=0.7):
    provider = provider.lower()
    
    # Grab secrets from code, env, or config
    openai_api_key = os.getenv("OPENAI_API_KEY")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    cohere_api_key = os.getenv("COHERE_API_KEY")
    huggingface_api_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_name or "gpt-3.5-turbo",
            temperature=temperature,
            api_key=openai_api_key  # explicit
        )

    elif provider == "anthropic":
        from langchain_community.chat_models import ChatAnthropic
        return ChatAnthropic(
            model=model_name or "claude-2",
            temperature=temperature,
            api_key=anthropic_api_key  # explicit
        )

    elif provider == "cohere":
        from langchain_community.llms import Cohere
        return Cohere(
            model=model_name or "command",
            temperature=temperature,
            cohere_api_key=cohere_api_key  # explicit
        )

    elif provider == "huggingface-hub":
        from langchain_community.llms import HuggingFaceHub
        return HuggingFaceHub(
            repo_id=model_name or "gpt2",
            huggingfacehub_api_token=huggingface_api_token,
            model_kwargs={"temperature": temperature}
        )

    elif provider == "huggingface-local":
        from langchain_community.llms import HuggingFacePipeline
        from transformers import AutoTokenizer, pipeline, AutoModelForCausalLM
        tokenizer = AutoTokenizer.from_pretrained(model_name or "gpt2")
        model = AutoModelForCausalLM.from_pretrained(model_name or "gpt2")
        pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=500)
        return HuggingFacePipeline(pipeline=pipe)

    else:
        raise Exception(f"Unsupported provider: {provider}")

# Prompt template
prompt_template = PromptTemplate.from_template(
    "You are an expert newsletter writer. Write a brief newsletter for {audience}.\n"
    "Include the following facts: {stats}\n\n"
    "Format:\nSubject: <subject line>\n\nBody:\n<email body>"
)

# Save PDF
def generate_pdf(subject, body):
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

# Azure Function
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
        chain = LLMChain(llm=llm, prompt=prompt_template)

        # Generate content
        raw_output = chain.run({"audience": audience, "stats": stats})
        if "Subject:" in raw_output and "Body:" in raw_output:
            subject = raw_output.split("Subject:")[1].split("Body:")[0].strip()
            body = raw_output.split("Body:")[1].strip()
        else:
            subject, body = "Newsletter Template", raw_output.strip()

        # Generate PDF
        pdf_stream = generate_pdf(subject, body)

        # Build response
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

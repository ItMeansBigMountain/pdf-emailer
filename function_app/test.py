import os
import smtplib
from utils import initialize_llm, generate_pdf, send_email, newsletter_prompt


def extract_subject_body(raw_output: str) -> tuple[str, str]:
    """Parses raw LLM output into subject and body."""
    if "Subject:" in raw_output and "Body:" in raw_output:
        subject = raw_output.split("Subject:")[1].split("Body:")[0].strip()
        body = raw_output.split("Body:")[1].strip()
    else:
        subject = "Newsletter Template"
        body = raw_output.strip()
    return subject, body


def generate_newsletter(provider: str = "openai", model: str = "gpt-3.5-turbo", temperature: float = 0.7) -> tuple[str, str]:
    """Generates a newsletter's subject and body for a given audience and stats."""

    # Define input variables for the prompt
    audience = "martial artists looking to boost recovery"
    stats = "studies show 85% of athletes improved recovery with supplements"
    tone = "witty and hype"
    cta = "Listen to our podcast for more insights"
    cta_note = "like and subscribe to our social media"
    title = "🏆 Recover Faster, Train Harder"

    # Format the prompt using the template
    prompt = newsletter_prompt.format(
        audience=audience,
        stat=stats,
        tone=tone,
        cta=cta,
        cta_note=cta_note,
        title=title,
    )

    # Initialize the LLM
    llm = initialize_llm(provider=provider, model_name=model, temperature=temperature)

    # Invoke the LLM with the formatted prompt
    raw_output = llm.invoke(prompt).content

    # Extract subject and body from the LLM output
    return extract_subject_body(raw_output)


if __name__ == "__main__":
    try:
        # Generate the newsletter
        subject, body = generate_newsletter(provider="openai", model="gpt-3.5-turbo", temperature=0.7)

        # Generate PDF from the subject and body
        pdf_bytes = generate_pdf(subject, body)

        # Send the email with the generated newsletter
        send_email(subject, body, pdf_bytes)

        print("Generated Newsletter:\n")
        print(f"Subject: {subject}\n")
        print(f"Body:\n{body}")
    except Exception as e:
        print(f"Error: {e}")
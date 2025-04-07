import os
import smtplib
from utils import initialize_llm, prompt_template , generate_pdf, send_email, newsletter_prompt


def extract_subject_body(raw_output: str) -> tuple[str, str]:
    """Parses raw LLM output into subject and body."""
    if "Subject:" in raw_output and "Body:" in raw_output:
        subject = raw_output.split("Subject:")[1].split("Body:")[0].strip()
        body = raw_output.split("Body:")[1].strip()
    else:
        subject = "Newsletter Template"
        body = raw_output.strip()
    return subject, body

def generate_newsletter(audience: str, stats: str, provider: str = "openai", model: str = "gpt-3.5-turbo", temperature: float = 0.7) -> tuple[str, str]:
    """Generates a newsletter's subject and body for a given audience and stats."""
    llm = initialize_llm(provider=provider, model_name=model, temperature=temperature)
    chain = prompt_template | llm
    raw_output = chain.invoke({"audience": audience, "stats": stats}).content
    return extract_subject_body(raw_output)




if __name__ == "__main__":
    audience = "seasoned martial artists"
    stats = (
        "Supplements have changed the game for athletes, improving recovery and performance. "
        "Research on testosterone boosters shows they can increase muscle mass and strength, "
        "especially in older adults. However, the effectiveness of these supplements can vary "
        "based on individual factors and the specific product used."
    )

        # Example usage:
    filled_prompt = newsletter_prompt.format(
        audience="martial artists looking to boost recovery",
        stat="studies show 85% of athletes improved recovery with supplements",
        tone="witty and hype",
        cta="Listen to our podcast for more insights",
        cta_note= "like and subscribe to our social media",
        title="🏆 Recover Faster, Train Harder"
    )
    print(filled_prompt)

    

    subject, body = generate_newsletter( filled_prompt , provider="openai", model="gpt-3.5-turbo", temperature=0.7)


    # Generate PDF from the subject and body
    pdf_bytes = generate_pdf(subject, body)

    # Send the email with the generated newsletter
    send_email(subject, body, pdf_bytes)

    print("Generated Newsletter:\n")
    print(f"Subject: {subject}\n")
    print(f"Body:\n{body}")

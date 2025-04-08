import os
from utils import initialize_llm, send_email, newsletter_prompt, extract_subject_body


def generate_newsletter(provider: str = "openai", model: str = "gpt-3.5-turbo", temperature: float = 0.7) -> tuple[str, str]:
    """Generates a newsletter's subject and body for a given audience and stats."""

    # Define input variables for the prompt
    audience = "martial artists looking to boost recovery"
    stats = "studies show 85% of athletes improved recovery with supplements"
    tone = "witty and hype. adult themed"
    cta = "go out there and talk to 5 women about having a good time"
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
    print(prompt);exit()

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
        print(f"{"-"*50}\nGenerated Newsletter")
        
        # Send the email with the generated newsletter
        send_email(subject, body)
        print(f"Subject: {subject}\n")
        print(f"Body Preview:\n{body[:100]}...\n")

    except Exception as e:
        print(f"Error: {e}")
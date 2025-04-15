import os
import requests
import pytest
from dotenv import load_dotenv

load_dotenv(".env")

BASE_URL = "https://" + os.getenv("AZURE_FUNCTION_BASE_URL")
FUNCTION_KEY = os.getenv("AZURE_FUNCTION_KEY")


@pytest.fixture
def newsletter_payload():
    return {
        "provider": "openai",
        "model": "gpt-3.5-turbo",
        "temperature": 0.7,
        "title": "🏆 Recover Faster, Train Harder",
        "audience": "martial artists looking to boost recovery",
        "stats": "studies show 85% of athletes improved recovery with supplements",
        "tone": "witty and hype",
        "cta": "Listen to our podcast for more insights",
        "cta_note": "like and subscribe to our social media",
        "custom_prompt": "write a newsletter for a martial arts gym",
        "recipients": "example1@gmail.com,example2@gmail.com"
    }


def test_generate_newsletter_endpoint(newsletter_payload):
    response = requests.post(
        f"{BASE_URL}/api/generate-newsletter?code={FUNCTION_KEY}",
        json=newsletter_payload
    )

    print(f"Response Status Code: {response.status_code}")
    print(f"Response Text: {response.content.decode('utf-8')}")
    print(f"Request URL: {response.url}")

    assert response.status_code == 200
    assert "Newsletter sent successfully!" in response.text
    assert "Subject:" in response.text
    assert "Body :" in response.text

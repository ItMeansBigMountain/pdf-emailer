import os
import requests
import pytest
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture
def get_env_vars():
    base_url = os.getenv("AZURE_FUNCTION_BASE_URL")
    function_key = os.getenv("AZURE_FUNCTION_KEY")

    return {
        "BASE_URL": "https://" + base_url,
        "FUNCTION_KEY": function_key
    }


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


def test_generate_newsletter_endpoint(get_env_vars, newsletter_payload):
    BASE_URL = get_env_vars["BASE_URL"]
    FUNCTION_KEY = get_env_vars["FUNCTION_KEY"]

    response = requests.post(
        # f"{BASE_URL}/api/generate-newsletter?code={FUNCTION_KEY}",
        f"{BASE_URL}/api/generate-newsletter",
        json=newsletter_payload
    )

    print(f"Response Status Code: {response.status_code}")
    print(f"Response Text: {response.content.decode('utf-8')}")
    print(f"Request URL: {response.url}")

    assert response.status_code == 200
    assert "Newsletter sent successfully!" in response.text
    assert "Subject:" in response.text
    assert "Body :" in response.text
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_env_vars():
    base_url = os.getenv("AZURE_FUNCTION_BASE_URL")
    function_key = os.getenv("AZURE_FUNCTION_KEY")

    return {
        "BASE_URL": "https://" + base_url,
        "FUNCTION_KEY": function_key
    }

def get_newsletter_payload():
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

def main():
    env_vars = get_env_vars()
    BASE_URL = env_vars["BASE_URL"]
    FUNCTION_KEY = env_vars["FUNCTION_KEY"]

    payload = get_newsletter_payload()

    try:
        response = requests.post(
            f"{BASE_URL}/api/generate-newsletter?code={FUNCTION_KEY}",
            json=payload
        )

        print(f"Response Status Code: {response.status_code}")
        print(f"Response Text: {response.content.decode('utf-8')}")
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
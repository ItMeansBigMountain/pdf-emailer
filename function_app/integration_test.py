import os
import requests
import unittest

from dotenv import load_dotenv
load_dotenv(".env")


class TestPostDeploymentValidation(unittest.TestCase):
    BASE_URL = "https://" + os.getenv("AZURE_FUNCTION_BASE_URL")  
    FUNCTION_KEY = os.getenv("AZURE_FUNCTION_KEY")  

    def test_generate_newsletter_endpoint(self):
        """Test if the generate-newsletter endpoint is working and validates the response."""
        payload = {
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
        response = requests.post(
            f"{self.BASE_URL}/api/generate-newsletter?code={self.FUNCTION_KEY}",
            json=payload
        )

        # debug response
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Text: {response.content.decode('utf-8')}")
        print(f"request URL: {response.url}")

        # Check if the response is successful
        self.assertEqual(response.status_code, 200)
        self.assertIn("Newsletter sent successfully!", response.text)
        self.assertIn("Subject:", response.text)
        self.assertIn("Body :", response.text)

if __name__ == "__main__":
    unittest.main()
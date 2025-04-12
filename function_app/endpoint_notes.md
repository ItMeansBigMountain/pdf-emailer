# 📧 Azure PDF Emailer — Generate and Send AI-Powered Newsletters

This Azure Function allows you to generate AI-powered newsletters using LLMs (like OpenAI's GPT) and send them via email. It is designed to be highly customizable, enabling you to tailor the content, tone, and audience for your newsletters.

--- 

``` bash
curl -X POST https://pdf-emailer-func.azurewebsites.net/api/generate-newsletter -H "Content-Type: application/json" -d "{\"provider\":\"openai\",\"model\":\"gpt-3.5-turbo\",\"temperature\":0.7,\"title\":\"🏆 Recover Faster, Train Harder\",\"audience\":\"martial artists looking to boost recovery\",\"stats\":\"studies show 85% of athletes improved recovery with supplements\",\"tone\":\"witty and hype\",\"cta\":\"Listen to our podcast for more insights\",\"cta_note\":\"like and subscribe to our social media\",\"custom_prompt\":\"write a newsletter for a martial arts gym\",\"recipients\":\"trapiistan@gmail.com,thisguythinkstoomuch@yahoo.com\"}"
```



---

## 🌐 API Endpoint

### URL
`https://pdf-emailer-func.azurewebsites.net/api/generate-newsletter`

### HTTP Method
`POST`

---

## 🛠️ How to Use

### 1. **Request Headers**
Ensure the following header is included in your request:

```json
{
  "Content-Type": "application/json"
}
```

### 2. **Request Body**
The request body should be a JSON object with the following fields:

| Field           | Type     | Default Value               | Description                                                                 |
|------------------|----------|-----------------------------|-----------------------------------------------------------------------------|
| `provider`       | `string` | `"openai"`                 | The LLM provider to use (e.g., `openai`, `anthropic`, `cohere`, etc.).      |
| `model`          | `string` | `"gpt-3.5-turbo"`          | The specific model to use for content generation.                          |
| `temperature`    | `float`  | `0.7`                      | Controls the randomness of the output (higher = more creative).            |
| `title`          | `string` | `"Your Monthly Newsletter"`| The title or subject of the newsletter.                                    |
| `audience`       | `string` | `"a general audience"`     | The target audience for the newsletter.                                    |
| `stats`          | `string` | `""`                       | A statistic or fact to include in the newsletter for credibility.          |
| `tone`           | `string` | `"informative"`            | The tone of the newsletter (e.g., `witty`, `professional`, `casual`).      |
| `cta`            | `string` | `"Learn more on our website!"` | The call-to-action for the newsletter.                                     |
| `cta_note`       | `string` | `"Follow us for updates"`  | Additional notes for the call-to-action.                                   |
| `custom_prompt`  | `string` | `"Generate a newsletter"`  | A custom prompt to guide the LLM in generating the content.                |
| `recipients`     | `string` | Environment variable value | A comma-separated list of email recipients.                                |

### Example Request Body
```json
{
  "provider": "openai",
  "model": "gpt-3.5-turbo",
  "temperature": 0.7,
  "title": "🏆 Recover Faster, Train Harder",
  "audience": "martial artists looking to boost recovery",
  "stats": "Studies show 85% of athletes improved recovery with supplements.",
  "tone": "witty and hype",
  "cta": "Listen to our podcast for more insights",
  "cta_note": "Like and subscribe to our social media",
  "custom_prompt": "Write a newsletter for a martial arts gym",
  "recipients": "example1@gmail.com,example2@yahoo.com"
}
```

---

## 📤 Response

### Success Response
If the newsletter is successfully generated and sent, the API will return:

- **Status Code:** `200 OK`
- **Response Body:**
```plaintext
Newsletter sent successfully!

Subject: [Generated Subject]
Body: [Generated Body]
Recipients: [Recipient List]
```

### Error Response
If an error occurs, the API will return:

- **Status Code:** `500 Internal Server Error`
- **Response Body:**
```plaintext
Error: [Error Message]
```

---

## 🧪 Testing Locally

You can test the Azure Function locally using `curl` or any API testing tool like Postman.

### Example `curl` Command
```bash
curl -X POST https://pdf-emailer-func.azurewebsites.net/api/generate-newsletter \
-H "Content-Type: application/json" \
-d '{
  "provider": "openai",
  "model": "gpt-3.5-turbo",
  "temperature": 0.7,
  "title": "🏆 Recover Faster, Train Harder",
  "audience": "martial artists looking to boost recovery",
  "stats": "Studies show 85% of athletes improved recovery with supplements.",
  "tone": "witty and hype",
  "cta": "Listen to our podcast for more insights",
  "cta_note": "Like and subscribe to our social media",
  "custom_prompt": "Write a newsletter for a martial arts gym",
  "recipients": "example1@gmail.com,example2@yahoo.com"
}'
```

---

## 🔐 Environment Variables

The following environment variables must be configured for the Azure Function to work:

| Variable Name          | Description                           |
|-------------------------|---------------------------------------|
| `EMAIL_FROM`           | The sender's email address.           |
| `EMAIL_RECIPIENTS`     | Default recipients (comma-separated). |
| `SMTP_SERVER`          | SMTP server address (e.g., Gmail).    |
| `SMTP_PORT`            | SMTP server port (e.g., `587`).       |
| `SMTP_USERNAME`        | SMTP username (email address).        |
| `SMTP_PASSWORD`        | SMTP password or app-specific password. |
| `OPENAI_API_KEY`       | API key for OpenAI.                   |
| `HUGGINGFACEHUB_API_TOKEN` | API token for Hugging Face Hub.    |
| `ANTHROPIC_API_KEY`    | API key for Anthropic.                |
| `COHERE_API_KEY`       | API key for Cohere.                   |

---

## 🛡️ Error Handling

- **Invalid Request:** Ensure all required fields are included in the request body.
- **Email Sending Issues:** Verify SMTP credentials and recipient email addresses.
- **LLM Errors:** Check the API key and model configuration for the selected provider.

---

## 📚 Additional Notes

- This function is designed to be deployed on Azure using Terraform. Refer to the [setup guide](./docs/setup_guide.md) for deployment instructions.
- For cost analysis and architecture details, see the [cost analysis document](./docs/cost_analysis.md).

---

## 🛠️ Development

To modify or test the function locally:
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r function_app/requirements.txt
   ```
3. Run the function locally:
   ```bash
   func start
   ```
4. Test the endpoint using the example `curl` command above.

---



# 📧 Azure PDF Emailer — AI-Powered Newsletter Delivery System

Generate beautifully written AI newsletters and send them via email — all automated in the cloud using Azure Functions and Terraform.

GitHub Repo: [ItMeansBigMountain/pdf-emailer](https://github.com/ItMeansBigMountain/pdf-emailer)

---

## 🚀 What Is This?

This is a **serverless application** that:
- Uses LLMs (like OpenAI) to generate high-quality marketing newsletters.
- Formats them in Markdown, converts to HTML.
- Sends them to your mailing list via email.
- Can be deployed to Azure with 1 command using Terraform.

Perfect for:
- Content creators
- Small businesses
- Agencies with client email lists
- Anyone wanting automated, personalized content sent out daily/weekly/monthly

---

## 🧠 Key Features

| Feature | Description |
|--------|-------------|
| **LLM-generated Content** | Dynamically generated using OpenAI, Anthropic, Cohere, HuggingFace. |
| **Markdown-to-HTML** | Emails support modern styling for readability. |
| **Email via SMTP** | Easily configurable with Gmail, Outlook, or any SMTP server. |
| **Azure Functions** | Automatically runs on the cloud; scheduled or HTTP-triggered. |
| **Terraform Infrastructure** | One-command deploys your full cloud backend. |
| **Multimodel Support** | Plug in different LLMs to test style and tone. |
| **Prompt Templates** | Customizable audience, tone, call-to-action, etc. |

---

## 📂 Project Structure

```
.
├── function_app/
│   ├── __init__.py            # Azure Function entrypoint
│   ├── test.py                # Local script to test generation + send
│   ├── utils.py               # LLM integration, email sender, prompt template
│   ├── requirements.txt       # Python dependencies
│   └── host.json              # Azure config
├── infra/
│   ├── main.tf, variables.tf  # Terraform configs for Azure infra
├── .env                       # Your secret SMTP + API keys
```

---

## ⚙️ Prerequisites

- Python 3.10+
- Azure CLI
- Terraform
- An SMTP-enabled email (e.g., Gmail with App Passwords)
- OpenAI or other LLM API keys

---

## 🛠️ Setup Guide

### 1. Clone & Setup

```bash
git clone https://github.com/ItMeansBigMountain/pdf-emailer.git
cd pdf-emailer/function_app
pip install -r requirements.txt
```

### 2. Configure Environment Variables

To run `test.py` locally, create a `.env` file in `function_app/` with:

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your@email.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=your@email.com
EMAIL_RECIPIENTS=recipient1@example.com,recipient2@example.com

# LLM API keys
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
COHERE_API_KEY=your-cohere-key
HUGGINGFACEHUB_API_TOKEN=your-huggingface-key
```

The `.env` file is used to load all necessary credentials for LLM vendors and email delivery when running the system locally.

To set these credentials for the deployed cloud system, use `terraform.tfvars` inside the `infra/` folder. These map directly to Azure App Settings so your deployed Azure Function has access to the same credentials in a secure manner.

Example Terraform Variables:

```hcl
smtp_username = "your@email.com"
smtp_password = "your-app-password"
email_from    = "your@email.com"
email_recipients = "recipient1@example.com,recipient2@example.com"
OPENAI_API_KEY    = "sk-xxx"
```

---

## 🧪 Test Locally

Run the test script to see a sample newsletter and send it:

```bash
python test.py
```

This uses hardcoded sample values. Customize `test.py` to experiment with tones, audiences, or call-to-actions.

---

## ☁️ Deploy to Azure

### 1. Configure Terraform

Edit `infra/terraform.tfvars` with your Azure details and credentials.

### 2. Deploy Infrastructure

```bash
cd infra
terraform init
terraform apply
```

### 3. Deploy Function

```bash
cd ../function_app
func azure functionapp publish pdf-emailer-func
```

### 4. Call Your Endpoint

```bash
curl -X POST https://<your-func-app>.azurewebsites.net/api/generate-newsletter \
     -H "Content-Type: application/json" \
     -d '{
           "audience": "startup founders",
           "stats": "90% say newsletters help them discover tools",
           "tone": "inspirational",
           "cta": "Join our private community",
           "cta_note": "forward this to a founder friend",
           "title": "🚀 Founders Who Read, Lead"
         }'
```

---

## 📈 Planned Features

| Feature | Description |
|--------|-------------|
| 📁 Upload Email List | Accept CSV/JSON/TXT to bulk send to lists. |
| 👥 Multi-client Support | Send personalized newsletters per client via large CSV. |
| 🔄 Automatic Data Gathering | Scrape data from trusted sources (e.g. CNBC, Hacker News). |
| 🧠 Source Management | UI or config to add/remove RSS/news sources. |
| 🗓️ Subscription Engine | End-users subscribe and get emails regularly. |

---

## 🤝 Contributing

Want to help build auto-sourced newsletters, integrate vector databases, or plug in new providers? PRs welcome!

---

## 📝 License

MIT


# pdf-emailer-func

> A serverless Azure Function that generates AI-powered newsletters and sends them via email. 🌍📧

---

## 📊 Overview

This Azure Function app leverages OpenAI's GPT models to create marketing newsletters and deliver them through email. Built with scalability and modularity in mind, it supports multiple AI providers and is deployable with GitHub Actions.

---

## 🌐 Live Deployment

| Item | Value |
|:----|:------|
| URL | `https://pdf-emailer-func.azurewebsites.net/api/generate-newsletter` |
| Auth Level | Anonymous with Function Key |

### Trigger
- **HTTP POST** request
- JSON payload (audience, title, tone, stats, etc.)

---

## 🧹 Features

- ✨ AI Newsletter Generation (ChatGPT primary, failover to Anthropic, Cohere, HuggingFace)
- 📧 Email Sending with Markdown support
- ✨ Configurable via `.env`
- 🚀 Automated CI/CD (GitHub Actions)
- 🔄 Integration Test Included

---

## 📂 Architecture

```mermaid
graph LR
    A[HTTP Request] --> B[Azure Function Endpoint]
    B --> C[Prompt Engineering]
    C --> D[LLM Provider (OpenAI, etc)]
    D --> E[Generate Newsletter Content]
    E --> F[Convert Markdown to HTML]
    F --> G[SMTP Send Email]
```

---

## 📅 Cost Analysis

| Item | Cost |
|:-----|:-----|
| Azure Function Execution | ~$0 (under free grant) |
| LLM API Usage (OpenAI GPT-3.5-turbo) | ~$0.002–$0.004 per request |
| SMTP Email Sending (Gmail) | Free under daily limit |

> Estimated: ~$2–40 per 1,000–10,000 newsletters monthly

[Full Cost Breakdown Here](#)

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set environment variables
cp .env.example .env

# 3. Test locally
python local_llm_test.py

# 4. Deploy to Azure via GitHub Actions
(handled automatically on push to main)
```

---

## 🔄 Scheduled Sending (Roadmap)
- Integrate external schedulers (GitHub Actions, Azure Logic Apps, or custom cron)
- Dynamic prompt size tuning to manage token usage
_we have the terraform variable adding this to the azure function as an environment variable so it could work by adding it to the azure function as a scheduled job_

---

## 🔧 Tech Stack
- Python 3.10
- Azure Functions
- LangChain
- OpenAI, Anthropic, Cohere, Hugging Face
- SMTP (Gmail)
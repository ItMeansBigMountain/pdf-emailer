# 📧 Azure PDF Emailer — AI-Powered Newsletter Delivery System

Generate beautifully written AI newsletters and send them via email — all automated in the cloud using Azure Functions and Terraform.

GitHub Repo: [ItMeansBigMountain/pdf-emailer](https://github.com/ItMeansBigMountain/pdf-emailer)

---

## 🚀 What Is This?

This is a **serverless application** that:
- Uses LLMs (like OpenAI) to generate high-quality marketing newsletters.
- Formats them in Markdown, converts them to HTML for email delivery.
- Sends them to your mailing list via SMTP.
- Can be deployed to Azure with Terraform for a fully automated cloud solution.

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
│   ├── host.json              # Azure Function configuration
│   └── .env                   # Local environment variables
├── infra/
│   ├── main.tf                # Terraform configuration for Azure resources
│   ├── variables.tf           # Terraform variables
│   ├── terraform.tfvars       # Terraform variable values (sensitive data)
│   ├── outputs.tf             # Terraform outputs
│   └── backend.tf             # Terraform backend configuration
├── docs/
│   ├──
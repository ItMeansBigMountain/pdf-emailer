# Project Structure
```
azure-pdf-emailer/
├── .gitignore               # Git ignore file
├── README.md                # Project documentation
├── function_app/
│   ├── function_app.py      # Main Azure Function code
│   ├── host.json            # Azure Function host configuration
│   ├── local.settings.json  # Local development settings (excluded from git)
│   ├── requirements.txt     # Python dependencies
│   └── .funcignore          # Azure Functions ignore file
├── infra/
│   ├── main.tf                  # Main Terraform configuration file
│   ├── variables.tf             # Terraform variables definition
│   ├── outputs.tf               # Terraform outputs definition
│   ├── terraform.tfvars         # Terraform variables values (excluded from git)
│   └── .README.md          # Azure Functions ignore file
├── scripts/
│   ├── deploy.sh            # Deployment automation script
│   └── test_email.py        # Script to test email functionality
├── docs/
│   ├── cost_analysis.md     # Detailed cost analysis
│   ├── setup_guide.md       # Step-by-step setup instructions
│   └── images/              # Documentation images
│       └── architecture.png # System architecture diagram
└── templates/
    └── email_template.html  # HTML template for emails
```



### 📄 `README.md` — Azure PDF Generator and Email Sender

# 📧 Azure PDF Generator and Email Sender

An Azure-based serverless app that uses Python to generate PDFs using LLMs and email them via SMTP on a scheduled basis.

---

## ✅ Prerequisites

- Azure account with active subscription
- [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) installed
- [Terraform](https://developer.hashicorp.com/terraform/install) installed
- [Git](https://git-scm.com/) installed
- [Azure Functions Core Tools](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local)

---

## 🚀 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-repo/azure-pdf-emailer.git
cd azure-pdf-emailer
```

### 2. Initialize Terraform

```bash
cd infra
terraform init
```

### 3. Configure Environment Variables

Create a file `terraform.tfvars`:

```hcl
SMTP_USERNAME     = "your-email@example.com"
SMTP_PASSWORD     = "your-email-password"
LLM_API_KEY       = "your-openai-api-key"
EMAIL_RECIPIENTS  = "recipient1@example.com,recipient2@example.com"
```

### 4. Define Python Dependencies

Create `requirements.txt` in the `function_app/` directory:

```txt
azure-functions
openai
fpdf
azure-storage-blob
```

---

## 📦 Deploy Infrastructure

```bash
cd infra
terraform apply
```

📌 **Note**: Save the function app URL from Terraform output.

---

## 🧠 Deploy the Function Code

```bash
cd function_app
func azure functionapp publish pdf-emailer-function --python
```

---

## ✅ Verify Deployment

1. Visit Azure Portal → Function App → Overview
2. Confirm function is running
3. Monitor logs under "Logs" tab
4. Wait for scheduled time to check email delivery

---

## 🔧 Troubleshooting

| Issue | Fix |
|-------|-----|
| Function not executing | Check logs in Azure Portal |
| Email not sending | Verify SMTP credentials + recipient emails |
| PDF not generated | Ensure OpenAI key is valid and reachable |

---

## 🔐 Best Practices

- 🔑 **Secrets** stored securely in Azure App Settings
- 📊 **Logging** enabled in Function App for debugging
- 🤖 **LLM** API key stored in environment, fallback if fails
- ✉️ **Email template** used from HTML file for flexibility

---

## 📚 Docs

- `docs/setup_guide.md`: Setup walkthrough
- `docs/cost_analysis.md`: Real usage and billing estimates
- `templates/email_template.html`: Editable email body
- `scripts/test_email.py`: Send test emails

---
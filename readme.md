# 📧 Azure PDF Emailer

An Azure-based serverless application that generates newsletters as PDFs using LLMs (Large Language Models) and sends them via email using SMTP. This project leverages Azure Functions, Terraform for infrastructure as code, and Python for the application logic.

---

## 📂 Project Structure

```
pdf-emailer/
├── .gitignore               # Files and directories to ignore in Git
├── README.md                # Project documentation
├── function_app/            # Azure Function application code
│   ├── __init__.py          # Entry point for the Azure Function
│   ├── utils.py             # Helper functions for PDF generation and LLM integration
│   ├── requirements.txt     # Python dependencies
│   ├── host.json            # Azure Function host configuration
│   ├── local.settings.json  # Local development settings (excluded from Git)
│   ├── .funcignore          # Files to ignore during Azure Function deployment
│   └── test.py              # Script for testing the function locally
├── infra/                   # Terraform configuration for Azure infrastructure
│   ├── main.tf              # Main Terraform configuration
│   ├── variables.tf         # Terraform variables definition
│   ├── outputs.tf           # Terraform outputs definition
│   ├── backend.tf           # Terraform backend configuration
│   ├── terraform.tfvars     # Terraform variable values (excluded from Git)
│   └── .terraform/          # Terraform state and provider files
├── templates/               # Email templates
│   └── email_template.html  # HTML template for email content
├── docs/                    # Documentation
│   ├── setup_guide.md       # Step-by-step setup instructions
│   ├── cost_analysis.md     # Cost analysis and optimization tips
│   └── images/              # Images for documentation
└── scripts/                 # Utility scripts
    └── deploy.sh            # Script for automating deployment
```

---

## ✅ Prerequisites

Before you begin, ensure you have the following:

- An Azure account with an active subscription
- [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) installed
- [Terraform](https://developer.hashicorp.com/terraform/downloads) installed
- [Python 3.10+](https://www.python.org/downloads/) installed
- [Azure Functions Core Tools](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local) installed
- [Git](https://git-scm.com/) installed

---

## 🚀 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-repo/pdf-emailer.git
cd pdf-emailer
```

### 2. Configure Environment Variables

Update the `infra/terraform.tfvars` file with your configuration:

```hcl
resource_group_name  = "pdf-emailer-rg"
location             = "East US"
smtp_username        = "your-email@example.com"
smtp_password        = "your-email-password"
email_from           = "notifications@yourcompany.com"
email_recipients     = "recipient1@example.com,recipient2@example.com"
OPENAI_API_KEY       = "your-openai-api-key"
schedule             = "0 0 9 * * *"
```

### 3. Install Python Dependencies

Navigate to the `function_app` directory and install the required Python packages:

```bash
cd function_app
pip install -r requirements.txt
```

### 4. Initialize Terraform

Navigate to the `infra` directory and initialize Terraform:

```bash
cd ../infra
terraform init
```

---

## 📦 Deployment

### 1. Deploy Infrastructure

Run the following command to deploy the Azure infrastructure:

```bash
terraform apply
```

Save the output, which includes the function app URL.

### 2. Deploy the Azure Function

Navigate to the `function_app` directory and deploy the function:

```bash
cd ../function_app
func azure functionapp publish <function-app-name> --python
```

---

## 🧪 Testing

### 1. Test Locally

Run the `test.py` script to test the newsletter generation locally:

```bash
python test.py
```

### 2. Verify Deployment

- Visit the Azure Portal and navigate to your Function App.
- Check the logs to ensure the function is running correctly.
- Verify that emails are being sent as expected.

---

## 🔧 Troubleshooting

| Issue                  | Possible Fix                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| Function not executing | Check the logs in the Azure Portal for errors.                             |
| Email not sending      | Verify SMTP credentials and recipient email addresses.                     |
| PDF not generated      | Ensure the LLM API key is valid and the model is reachable.                |
| Terraform errors       | Ensure Azure CLI is logged in and the correct subscription is selected.    |

---

## 🔐 Best Practices

- Store sensitive information (e.g., API keys, SMTP credentials) securely in Azure App Settings.
- Enable logging in the Azure Function for better debugging.
- Use a fallback mechanism for LLM failures to ensure reliability.
- Regularly monitor Azure costs and optimize resource usage.

---

## 📚 Documentation

- [Setup Guide](docs/setup_guide.md): Detailed setup instructions
- [Cost Analysis](docs/cost_analysis.md): Cost breakdown and optimization tips
- [Email Template](templates/email_template.html): Editable HTML email template

---

## 🛠️ Future Enhancements

- Add a web dashboard for managing newsletters and recipients.
- Implement analytics for email delivery and engagement.
- Support additional LLM providers and models.
- Add more robust error handling and retry mechanisms.

---

## 📝 License

This project is licensed under the [MIT License](LICENSE).

# Azure PDF Emailer Project - Todo List

## Initial Setup
- **Install required tools:**
  - Azure CLI
  - Terraform
  - Python 3.10+
  - Git
- **Create project folder structure:**
  - `azure-pdf-emailer/`
    - `function_app/`
    - `scripts/`
    - `docs/`

---

## Infrastructure Setup
- **Create Terraform files:**
  - `main.tf` (from provided code)
  - `variables.tf` (to define variables)
  - `outputs.tf` (for useful outputs)
  - `.gitignore` (include `terraform.tfvars`)
- **Configure Azure credentials:**
  - Login to Azure CLI
  - Set appropriate subscription
  - Create service principal (optional for CI/CD)

---

## Function App Development
- **Set up function app code:**
  - `function_app.py` (from provided code)
  - `requirements.txt` (with dependencies)
  - `host.json` (configuration file)
  - `.funcignore` file
- **Configure email template:**
  - `email_template.html`
  - Customize branding/styling

---

## LLM Integration
- Get OpenAI API key or configure alternative LLM provider
- Test LLM prompt for PDF content generation
- Create fallback content for LLM failures

---

## Deployment
- **Initialize Terraform environment:**
  - Run `terraform init`
  - Create `terraform.tfvars` with sensitive values
- **Deploy infrastructure:**
  - Run `terraform apply`
  - Verify resources in Azure Portal
- **Deploy function code:**
  - Navigate to `function_app/` directory
  - Run deployment command for function app

---

## Testing
- Test PDF generation locally
- Test email sending functionality
- Monitor first scheduled execution
- Verify PDF is correctly stored in blob storage

---

## Documentation
- Update `README.md` with project overview
- Document configuration options
- Create architecture diagram
- Document troubleshooting steps

---

## Optimization
- Review Azure costs after the first week
- Optimize LLM prompt for better content
- Improve PDF formatting and styling
- Consider additional features:
  - Web dashboard
  - Analytics
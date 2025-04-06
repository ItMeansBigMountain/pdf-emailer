provider "azapi" {
  # use this if using azurerm provider already
  # depends on Azure CLI context
}

provider "azurerm" {
  features {}
}

###########################################
output "subscription_id" {
  value = azapi_resource.subscription.output["properties.subscriptionId"]
}

resource "azapi_resource" "subscription" {
  type      = "Microsoft.Subscription/subscriptionCreationParameters@2021-10-01"
  name      = "example-sub"
  parent_id = "/providers/Microsoft.Subscription"

  body = jsonencode({
    displayName            = "My New Subscription"
    managementGroupId      = "/providers/Microsoft.Management/managementGroups/my-mg"
    workload               = "Production"  # or "DevTest"
    billingScope           = "/providers/Microsoft.Billing/billingAccounts/{billingAccountId}/billingProfiles/{billingProfileId}/invoiceSections/{invoiceSectionId}"
  })

  response_export_values = ["properties.subscriptionId"]
}

###########################################

resource "azurerm_resource_group" "pdf_emailer" {
  name     = "pdf-emailer-resources"
  location = "East US"
}

# Storage account for function app
resource "azurerm_storage_account" "pdf_emailer" {
  name                     = "pdfemailerstorage"
  resource_group_name      = azurerm_resource_group.pdf_emailer.name
  location                 = azurerm_resource_group.pdf_emailer.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

# App Service Plan for Function App
resource "azurerm_service_plan" "pdf_emailer" {
  name                = "pdf-emailer-service-plan"
  location            = azurerm_resource_group.pdf_emailer.location
  resource_group_name = azurerm_resource_group.pdf_emailer.name
  os_type             = "Linux"
  sku_name            = "Y1" # Consumption plan
}

# Function App
resource "azurerm_linux_function_app" "pdf_emailer" {
  name                       = "pdf-emailer-function"
  location                   = azurerm_resource_group.pdf_emailer.location
  resource_group_name        = azurerm_resource_group.pdf_emailer.name
  service_plan_id            = azurerm_service_plan.pdf_emailer.id
  storage_account_name       = azurerm_storage_account.pdf_emailer.name
  storage_account_access_key = azurerm_storage_account.pdf_emailer.primary_access_key

  site_config {
    application_stack {
      python_version = "3.10"
    }
  }

  app_settings = {
    "FUNCTIONS_WORKER_RUNTIME"     = "python"
    "SMTP_SERVER"                  = "smtp.office365.com"
    "SMTP_PORT"                    = "587"
    "SMTP_USERNAME"                = "@sensitive()"
    "SMTP_PASSWORD"                = "@sensitive()"
    "EMAIL_FROM"                   = "notifications@yourcompany.com"
    "LLM_API_KEY"                  = "@sensitive()"
    "LLM_ENDPOINT"                 = "https://api.openai.com/v1/chat/completions"
    "EMAIL_RECIPIENTS"             = "recipient1@example.com,recipient2@example.com"
    "SCHEDULE"                     = "0 0 9 * * *" # 9 AM daily
  }
}

# Storage container for generated PDFs
resource "azurerm_storage_container" "pdf_container" {
  name                  = "generated-pdfs"
  storage_account_name  = azurerm_storage_account.pdf_emailer.name
  container_access_type = "private"
}

# Output the function app default hostname
output "function_app_url" {
  value = azurerm_linux_function_app.pdf_emailer.default_hostname
}
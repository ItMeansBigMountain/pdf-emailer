provider "azapi" {
  # Used alongside azurerm provider
}

provider "azurerm" {
  features {}
}

###########################################
# Create a new Azure Subscription under a management group
resource "azapi_resource" "subscription" {
  type      = "Microsoft.Subscription/subscriptionCreationParameters@2021-10-01"
  name      = "example-sub"
  parent_id = "/providers/Microsoft.Subscription"

  body = jsonencode({
    displayName       = "My New Subscription"
    managementGroupId = var.management_group_id
    workload          = "Production"
    billingScope      = var.billing_scope
  })

  response_export_values = ["properties.subscriptionId"]
}

output "subscription_id" {
  value = azapi_resource.subscription.output["properties.subscriptionId"]
}

###########################################
# Resource Group
resource "azurerm_resource_group" "pdf_emailer" {
  name     = var.resource_group_name
  location = var.location
}

# Storage Account
resource "azurerm_storage_account" "pdf_emailer" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.pdf_emailer.name
  location                 = azurerm_resource_group.pdf_emailer.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

# App Service Plan
resource "azurerm_service_plan" "pdf_emailer" {
  name                = var.service_plan_name
  location            = azurerm_resource_group.pdf_emailer.location
  resource_group_name = azurerm_resource_group.pdf_emailer.name
  os_type             = "Linux"
  sku_name            = "Y1"
}

# Function App
resource "azurerm_linux_function_app" "pdf_emailer" {
  name                       = var.function_app_name
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
    "SMTP_USERNAME"                = var.smtp_username
    "SMTP_PASSWORD"                = var.smtp_password
    "EMAIL_FROM"                   = var.email_from
    "EMAIL_RECIPIENTS"             = var.email_recipients
    "LLM_API_KEY"                  = var.llm_api_key
    "LLM_ENDPOINT"                 = var.llm_endpoint
    "SCHEDULE"                     = var.schedule
  }
}

# PDF Output Container
resource "azurerm_storage_container" "pdf_container" {
  name                  = "generated-pdfs"
  storage_account_name  = azurerm_storage_account.pdf_emailer.name
  container_access_type = "private"
}

# Outputs
output "function_app_url" {
  value = azurerm_linux_function_app.pdf_emailer.default_hostname
}

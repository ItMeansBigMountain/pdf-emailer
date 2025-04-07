provider "azurerm" {
  features {}
  subscription_id = data.azurerm_subscription.Email_List_Subscription.id
}

output "current_subscription_id" {
  value = data.azurerm_subscription.Email_List_Subscription.id
}

resource "azurerm_resource_group" "pdf_emailer" {
  name     = var.resource_group_name
  location = var.location
}

resource "azurerm_storage_account" "pdf_emailer" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.pdf_emailer.name
  location                 = azurerm_resource_group.pdf_emailer.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_service_plan" "pdf_emailer" {
  name                = var.service_plan_name
  location            = var.location
  resource_group_name = var.resource_group_name
  os_type             = "Linux"
  sku_name            = "Y1"
}

resource "azurerm_linux_function_app" "pdf_emailer" {
  name                       = var.function_app_name
  location                   = var.location
  resource_group_name        = var.resource_group_name
  service_plan_id            = azurerm_service_plan.pdf_emailer.id
  storage_account_name       = azurerm_storage_account.pdf_emailer.name
  storage_account_access_key = azurerm_storage_account.pdf_emailer.primary_access_key

  site_config {
    application_stack {
      python_version = "3.10"
    }
  }

  app_settings = {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true"
    "FUNCTIONS_WORKER_RUNTIME" = "python"
    "SMTP_SERVER"              = "smtp.google.com"
    "SMTP_PORT"                = "587"
    "OPENAI_API_KEY"           = var.OPENAI_API_KEY
    "HUGGINGFACEHUB_API_TOKEN" = var.HUGGINGFACEHUB_API_TOKEN
    "ANTHROPIC_API_KEY"        = var.ANTHROPIC_API_KEY
    "COHERE_API_KEY"           = var.COHERE_API_KEY
    "SMTP_USERNAME"            = var.smtp_username
    "SMTP_PASSWORD"            = var.smtp_password
    "EMAIL_FROM"               = var.email_from
    "EMAIL_RECIPIENTS"         = var.email_recipients
    "SCHEDULE"                 = var.schedule
  }
}

resource "azurerm_storage_container" "pdf_container" {
  name                  = "generated-pdfs"
  storage_account_name  = azurerm_storage_account.pdf_emailer.name
  container_access_type = "private"
}

output "function_app_url" {
  value = azurerm_linux_function_app.pdf_emailer.default_hostname
}
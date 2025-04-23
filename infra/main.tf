provider "azurerm" {
  features {}
  subscription_id = var.AZURE_SUBSCRIPTION_ID
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

resource "azurerm_application_insights" "pdf_emailer" {
  name                = "${var.function_app_name}-ai"
  location            = var.location
  resource_group_name = var.resource_group_name
  application_type    = "web"
}

resource "azurerm_linux_function_app" "pdf_emailer" {
  depends_on                 = [azurerm_storage_account.pdf_emailer, azurerm_service_plan.pdf_emailer]
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
    "AzureWebJobsStorage"                   = azurerm_storage_account.pdf_emailer.primary_connection_string,
    "FUNCTIONS_WORKER_RUNTIME"              = "python",
    "SMTP_SERVER"                           = var.SMTP_SERVER,
    "SMTP_PORT"                             = var.SMTP_PORT,
    "OPENAI_API_KEY"                        = var.OPENAI_API_KEY,
    "HUGGINGFACEHUB_API_TOKEN"              = var.HUGGINGFACEHUB_API_TOKEN,
    "ANTHROPIC_API_KEY"                     = var.ANTHROPIC_API_KEY,
    "COHERE_API_KEY"                        = var.COHERE_API_KEY,
    "SMTP_USERNAME"                         = var.SMTP_USERNAME,
    "SMTP_PASSWORD"                         = var.SMTP_PASSWORD,
    "EMAIL_FROM"                            = var.EMAIL_FROM,
    "EMAIL_RECIPIENTS"                      = var.EMAIL_RECIPIENTS,
    "SCHEDULE"                              = var.schedule,
    "WEBSITE_RUN_FROM_PACKAGE"              = "1",
    "WEBSITE_ENABLE_APP_SERVICE_STORAGE"    = "false",
    "WEBSITE_REMOTE_DEBUGGING_ENABLED"      = "false",
    "WEBSITE_REMOTE_DEBUGGING_VERSION"      = "VS2019",
    "SCM_DO_BUILD_DURING_DEPLOYMENT"        = "true",
    "APPINSIGHTS_INSTRUMENTATIONKEY"        = azurerm_application_insights.pdf_emailer.instrumentation_key,
    "APPLICATIONINSIGHTS_CONNECTION_STRING" = azurerm_application_insights.pdf_emailer.connection_string
  }
}

resource "azurerm_storage_container" "pdf_container" {
  depends_on            = [azurerm_linux_function_app.pdf_emailer, azurerm_storage_account.pdf_emailer]
  name                  = "generated-pdfs"
  storage_account_id    = azurerm_storage_account.pdf_emailer.id
  container_access_type = "private"
}

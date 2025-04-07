variable "resource_group_name" {
  type        = string
  default     = "pdf-emailer-rg"
  description = "Name of the Azure Resource Group"
}

variable "location" {
  type        = string
  default     = "East US"
  description = "Azure region where resources will be deployed"
}

variable "storage_account_name" {
  type        = string
  default     = "pdfemailerstorage"
  description = "Unique name for the Azure Storage Account (must be globally unique)"
}

variable "service_plan_name" {
  type        = string
  default     = "pdf-emailer-plan"
  description = "App Service Plan name for the Azure Function"
}

variable "function_app_name" {
  type        = string
  default     = "pdf-emailer-func"
  description = "Name of the Azure Linux Function App"
}

variable "smtp_username" {
  type        = string
  description = "SMTP username (e.g., email account for sending)"
  sensitive   = true
}

variable "smtp_password" {
  type        = string
  description = "SMTP password"
  sensitive   = true
}

variable "email_from" {
  type        = string
  description = "Sender email address"
}

variable "email_recipients" {
  type        = string
  description = "Comma-separated recipient list"
}

variable "llm_api_key" {
  type        = string
  description = "API key for OpenAI or LLM provider"
  sensitive   = true
}

variable "llm_endpoint" {
  type        = string
  description = "Endpoint URL for the LLM provider"
}

variable "schedule" {
  type        = string
  default     = "0 0 9 * * *"
  description = "CRON expression for scheduling the Function"
}

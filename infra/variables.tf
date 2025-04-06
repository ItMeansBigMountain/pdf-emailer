variable "location" {
  type        = string
  default     = "East US"
  description = "Azure region where resources will be deployed"
}

variable "resource_group_name" {
  type        = string
  default     = "pdf-emailer-resources"
  description = "Name of the resource group"
}

variable "storage_account_name" {
  type        = string
  default     = "pdfemailerstorage"
  description = "Unique name for the Azure Storage account"
}

variable "service_plan_name" {
  type        = string
  default     = "pdf-emailer-service-plan"
  description = "App Service plan name for the Function App"
}

variable "function_app_name" {
  type        = string
  default     = "pdf-emailer-function"
  description = "Azure Function App name"
}

variable "management_group_id" {
  type        = string
  description = "ID of the Azure Management Group"
}

variable "billing_scope" {
  type        = string
  description = "Billing scope for the new Azure Subscription"
}

variable "smtp_username" {
  type        = string
  description = "SMTP username for sending emails"
  sensitive   = true
}

variable "smtp_password" {
  type        = string
  description = "SMTP password"
  sensitive   = true
}

variable "email_from" {
  type        = string
  description = "Email sender address"
}

variable "email_recipients" {
  type        = string
  description = "Comma-separated list of recipients"
}

variable "llm_api_key" {
  type        = string
  description = "API key for LLM provider (e.g., OpenAI)"
  sensitive   = true
}

variable "llm_endpoint" {
  type        = string
  description = "LLM endpoint (e.g., OpenAI Chat API)"
}

variable "schedule" {
  type        = string
  default     = "0 0 9 * * *"
  description = "CRON expression for the scheduled job"
}

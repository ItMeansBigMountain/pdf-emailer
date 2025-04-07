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

variable "schedule" {
  type        = string
  default     = "0 0 9 * * *"
  description = "CRON expression for scheduling the Function"
}

variable "OPENAI_API_KEY" {
  type        = string
  default     = ""
  description = "API KEYS FOR OPENAI_API_KEY"
}

variable "HUGGINGFACEHUB_API_TOKEN" {
  type        = string
  default     = ""
  description = "API KEYS FOR HUGGINGFACEHUB_API_TOKEN"
}

variable "ANTHROPIC_API_KEY" {
  type        = string
  default     = ""
  description = "API KEYS FOR ANTHROPIC_API_KEY"
}

variable "COHERE_API_KEY" {
  type        = string
  default     = ""
  description = "API KEYS FOR COHERE_API_KEY"
}

variable "SMTP_SERVER" {
  type        = string
  default     = "smtp.google.com"
  description = "SMTP server address"
}

variable "SMTP_PORT" {
  type        = string
  default     = "587"
  description = "SMTP server port"
}

variable "SMTP_USERNAME" {
  type        = string
  default     = "classicalechos@gmail.com"
  description = "SMTP username (email account for sending)"
  sensitive   = true
}

variable "SMTP_PASSWORD" {
  type        = string
  default     = "dgfx gvef qbbn bona"
  description = "SMTP password"
  sensitive   = true
}

variable "EMAIL_FROM" {
  type        = string
  default     = "classicalechos@gmail.com"
  description = "Sender email address"
}

variable "EMAIL_RECIPIENTS" {
  type        = string
  default     = "trapiistan@gmail.com,classical.echos@gmail.com"
  description = "Comma-separated recipient list"
}
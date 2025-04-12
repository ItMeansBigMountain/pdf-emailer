output "function_app_url" {
  value = azurerm_linux_function_app.pdf_emailer.default_hostname
}
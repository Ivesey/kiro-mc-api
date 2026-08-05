output "function_app_url" {
  value       = "https://${data.azurerm_linux_function_app.main.default_hostname}"
  description = "Full HTTPS URL of the Function App for WebUI configuration"
}

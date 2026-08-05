output "function_app_name" {
  value       = azurerm_linux_function_app.main.name
  description = "Function App resource name for deployment scripts"
}

output "function_app_default_hostname" {
  value       = azurerm_linux_function_app.main.default_hostname
  description = "Default hostname of the Function App (e.g., {name}.azurewebsites.net)"
}

output "identity_principal_id" {
  value       = azurerm_linux_function_app.main.identity[0].principal_id
  description = "System-assigned managed identity principal ID for IAM role assignments"
}

output "function_app_id" {
  value       = azurerm_linux_function_app.main.id
  description = "Function App resource ID for CORS configuration by the networking module"
}

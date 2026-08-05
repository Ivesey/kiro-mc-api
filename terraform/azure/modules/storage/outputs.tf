output "storage_account_name" {
  value       = azurerm_storage_account.web.name
  description = "Storage account name for deployment scripts to upload WebUI assets to $web container"
}

output "primary_web_endpoint" {
  value       = azurerm_storage_account.web.primary_web_endpoint
  description = "Static website primary endpoint URL (origin for CDN)"
}

output "primary_web_host" {
  value       = azurerm_storage_account.web.primary_web_host
  description = "Static website hostname without protocol (for CDN origin)"
}

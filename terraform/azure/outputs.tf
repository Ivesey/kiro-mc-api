# Outputs will be populated as modules are added in subsequent tasks.

output "function_app_url" {
  value       = "https://${module.compute.function_app_default_hostname}"
  description = "Function App HTTPS URL for WebUI configuration to set API base endpoint"
}

output "cdn_url" {
  value       = "https://${module.cdn.cdn_endpoint_hostname}"
  description = "Azure CDN endpoint HTTPS URL for WebUI access"
}

output "storage_account_name" {
  value       = module.storage.storage_account_name
  description = "Storage account name for deployment scripts to upload WebUI assets to $web container"
}

output "cdn_profile_name" {
  value       = module.cdn.cdn_profile_name
  description = "CDN profile name for deployment scripts to purge cache"
}

output "cdn_endpoint_name" {
  value       = module.cdn.cdn_endpoint_name
  description = "CDN endpoint name for deployment scripts to purge cache"
}

output "resource_group_name" {
  value       = azurerm_resource_group.main.name
  description = "Resource group name for deployment scripts to reference Azure resources"
}

output "cosmosdb_endpoint" {
  value       = module.database.cosmosdb_endpoint
  description = "Cosmos DB endpoint URL for application configuration"
}

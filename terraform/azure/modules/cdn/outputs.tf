output "cdn_endpoint_hostname" {
  value       = azurerm_cdn_endpoint.main.fqdn
  description = "CDN endpoint hostname (e.g., {name}.azureedge.net) for WebUI access"
}

output "cdn_profile_name" {
  value       = azurerm_cdn_profile.main.name
  description = "CDN profile name for deployment scripts to purge cache"
}

output "cdn_endpoint_name" {
  value       = azurerm_cdn_endpoint.main.name
  description = "CDN endpoint name for deployment scripts to purge cache"
}

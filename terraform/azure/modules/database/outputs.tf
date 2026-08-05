output "cosmosdb_endpoint" {
  value       = azurerm_cosmosdb_account.main.endpoint
  description = "Cosmos DB account endpoint URL for application configuration"
}

output "cosmosdb_primary_key" {
  value       = azurerm_cosmosdb_account.main.primary_key
  description = "Cosmos DB primary key for application authentication"
  sensitive   = true
}

output "cosmosdb_database_name" {
  value       = azurerm_cosmosdb_sql_database.main.name
  description = "Cosmos DB database name for application configuration"
}

output "cosmosdb_container_name" {
  value       = azurerm_cosmosdb_sql_container.main.name
  description = "Cosmos DB container name for application configuration"
}

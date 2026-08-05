resource "azurerm_cosmosdb_account" "main" {
  name                = "${var.environment}-${var.project_name}-cosmos"
  location            = var.azure_region
  resource_group_name = var.resource_group_name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"

  consistency_policy {
    consistency_level = var.consistency_level
  }

  geo_location {
    location          = var.azure_region
    failover_priority = 0
  }

  dynamic "capabilities" {
    for_each = var.capacity_mode == "Serverless" ? [1] : []
    content {
      name = "EnableServerless"
    }
  }

  tags = var.tags
}

resource "azurerm_cosmosdb_sql_database" "main" {
  name                = var.database_name
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.main.name

  throughput = var.capacity_mode == "Provisioned" ? 400 : null
}

resource "azurerm_cosmosdb_sql_container" "main" {
  name                = var.container_name
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_sql_database.main.name
  partition_key_paths = [var.partition_key_path]

  throughput = var.capacity_mode == "Provisioned" ? 400 : null
}

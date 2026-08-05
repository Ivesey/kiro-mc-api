locals {
  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "terraform"
  }
}

resource "azurerm_resource_group" "main" {
  name     = "${var.environment}-${var.project_name}-rg"
  location = var.azure_region
  tags     = local.common_tags
}

module "storage" {
  source              = "./modules/storage"
  environment         = var.environment
  project_name        = var.project_name
  resource_group_name = azurerm_resource_group.main.name
  azure_region        = var.azure_region
  tags                = local.common_tags
}

module "database" {
  source              = "./modules/database"
  environment         = var.environment
  project_name        = var.project_name
  resource_group_name = azurerm_resource_group.main.name
  azure_region        = var.azure_region
  consistency_level   = var.cosmosdb_consistency_level
  capacity_mode       = var.cosmosdb_capacity_mode
  tags                = local.common_tags
}

module "compute" {
  source                  = "./modules/compute"
  environment             = var.environment
  project_name            = var.project_name
  resource_group_name     = azurerm_resource_group.main.name
  azure_region            = var.azure_region
  deployment_package_path = var.deployment_package_path
  cors_allowed_origins    = var.cors_allowed_origins

  app_settings = merge(var.app_environment_variables, {
    COSMOSDB_ENDPOINT       = module.database.cosmosdb_endpoint
    COSMOSDB_KEY            = module.database.cosmosdb_primary_key
    COSMOSDB_DATABASE_NAME  = module.database.cosmosdb_database_name
    COSMOSDB_CONTAINER_NAME = module.database.cosmosdb_container_name
    DAL_IMPLEMENTATION      = "azure_dal.cosmosdb_case_dal.CosmosDBCaseDAL"
  })

  tags = local.common_tags
}

module "cdn" {
  source              = "./modules/cdn"
  environment         = var.environment
  project_name        = var.project_name
  resource_group_name = azurerm_resource_group.main.name
  azure_region        = var.azure_region
  origin_host_name    = module.storage.primary_web_host
  tags                = local.common_tags
}

module "networking" {
  source               = "./modules/networking"
  function_app_id      = module.compute.function_app_id
  cors_allowed_origins = var.cors_allowed_origins
}

locals {
  # Storage account naming for Functions: alphanumeric, lowercase, max 24 characters
  # Pattern: {env}{short}func where short is derived from project_name
  # For "microdigitech-cases" -> "mcases" (first letter of each segment except last + last segment)
  project_parts = split("-", var.project_name)
  project_short = join("", [
    for i, part in local.project_parts :
    i < length(local.project_parts) - 1 ? substr(part, 0, 1) : part
  ])

  # Build the storage account name: {env}{short}func, truncated to 24 chars max
  raw_func_storage_name = "${var.environment}${local.project_short}func"
  func_storage_name = substr(
    lower(replace(local.raw_func_storage_name, "/[^a-z0-9]/", "")),
    0,
    min(24, length(lower(replace(local.raw_func_storage_name, "/[^a-z0-9]/", ""))))
  )
}

resource "azurerm_service_plan" "main" {
  name                = "${var.environment}-${var.project_name}-plan"
  resource_group_name = var.resource_group_name
  location            = var.azure_region
  os_type             = "Linux"
  sku_name            = "Y1"

  tags = var.tags
}

resource "azurerm_storage_account" "func" {
  name                     = local.func_storage_name
  resource_group_name      = var.resource_group_name
  location                 = var.azure_region
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = var.tags
}

resource "azurerm_linux_function_app" "main" {
  name                = "${var.environment}-${var.project_name}-func"
  resource_group_name = var.resource_group_name
  location            = var.azure_region
  service_plan_id     = azurerm_service_plan.main.id

  storage_account_name       = azurerm_storage_account.func.name
  storage_account_access_key = azurerm_storage_account.func.primary_access_key

  zip_deploy_file = var.deployment_package_path

  app_settings = var.app_settings

  site_config {
    application_stack {
      python_version = "3.12"
    }

    cors {
      allowed_origins     = var.cors_allowed_origins
      support_credentials = false
    }
  }

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

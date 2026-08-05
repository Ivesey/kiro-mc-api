locals {
  # Storage account naming: alphanumeric, lowercase, max 24 characters
  # Pattern: {env}{short}web where short is derived from project_name
  # For "microdigitech-cases" -> "mcases" (first letter of each segment except last + last segment)
  project_parts = split("-", var.project_name)
  project_short = join("", [
    for i, part in local.project_parts :
    i < length(local.project_parts) - 1 ? substr(part, 0, 1) : part
  ])

  # Build the storage account name: {env}{short}web, truncated to 24 chars max
  raw_storage_name = "${var.environment}${local.project_short}web"
  storage_account_name = substr(
    lower(replace(local.raw_storage_name, "/[^a-z0-9]/", "")),
    0,
    min(24, length(lower(replace(local.raw_storage_name, "/[^a-z0-9]/", ""))))
  )
}

resource "azurerm_storage_account" "web" {
  name                     = local.storage_account_name
  resource_group_name      = var.resource_group_name
  location                 = var.azure_region
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = var.tags
}

resource "azurerm_storage_account_static_website" "web" {
  storage_account_id = azurerm_storage_account.web.id
  index_document     = "index.html"
}

terraform {
  backend "azurerm" {
    # Configuration provided via -backend-config flags during terraform init:
    # resource_group_name  = "..."
    # storage_account_name = "..."
    # container_name       = "..."
    # key                  = "..."
  }
}

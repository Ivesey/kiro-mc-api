resource "azurerm_cdn_profile" "main" {
  name                = "${var.environment}-${var.project_name}-cdn"
  location            = var.azure_region
  resource_group_name = var.resource_group_name
  sku                 = "Standard_Microsoft"

  tags = var.tags
}

resource "azurerm_cdn_endpoint" "main" {
  name                = "${var.environment}-${var.project_name}-ep"
  profile_name        = azurerm_cdn_profile.main.name
  location            = var.azure_region
  resource_group_name = var.resource_group_name

  origin {
    name      = "storage-origin"
    host_name = var.origin_host_name
  }

  origin_host_header = var.origin_host_name

  delivery_rule {
    name  = "HttpsRedirect"
    order = 1

    request_scheme_condition {
      operator     = "Equal"
      match_values = ["HTTP"]
    }

    url_redirect_action {
      redirect_type = "Found"
      protocol      = "Https"
    }
  }

  tags = var.tags
}

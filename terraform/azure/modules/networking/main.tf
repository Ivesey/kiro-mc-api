# CORS for Azure Functions is configured via site_config.cors on the Function App resource.
# In Azure, unlike AWS API Gateway, there is no separate CORS resource — allowed origins and
# methods are set directly in the Function App's site_config block (handled by the compute module).
#
# This module provides:
# 1. A CORS variable interface (cors_allowed_origins) for the root module to pass through
# 2. The function_app_url output derived from the Function App's default hostname
#
# The networking module exists for architectural consistency with the AWS networking module
# (which manages API Gateway as a separate resource) and to serve as the integration point
# for CORS configuration variables.
#
# CORS allowed methods: GET, POST, PUT, PATCH, DELETE, OPTIONS
# These are configured in the compute module's site_config.cors block.

data "azurerm_linux_function_app" "main" {
  name                = split("/", var.function_app_id)[8]
  resource_group_name = split("/", var.function_app_id)[4]
}

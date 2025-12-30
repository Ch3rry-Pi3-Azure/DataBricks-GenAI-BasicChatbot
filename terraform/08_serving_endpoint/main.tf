terraform {
  required_version = ">= 1.5"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.58"
    }
  }
}

provider "azurerm" {
  features {}
}

data "terraform_remote_state" "databricks" {
  backend = "local"
  config = {
    path = "../04_databricks_workspace/terraform.tfstate"
  }
}

data "azurerm_databricks_workspace" "main" {
  name                = data.terraform_remote_state.databricks.outputs.databricks_workspace_name
  resource_group_name = var.resource_group_name
}

provider "databricks" {
  host                        = data.azurerm_databricks_workspace.main.workspace_url
  azure_workspace_resource_id = data.azurerm_databricks_workspace.main.id
  auth_type                   = "azure-cli"
}

resource "databricks_model_serving" "main" {
  name = var.endpoint_name

  config {
    served_entities {
      name                 = var.served_model_name
      entity_name          = var.model_name
      entity_version       = var.model_version
      workload_size        = var.workload_size
      scale_to_zero_enabled = var.scale_to_zero_enabled
      environment_vars = {
        OPENAI_API_BASE         = "{{secrets/${var.secret_scope_name}/openai-api-base}}"
        OPENAI_API_KEY          = "{{secrets/${var.secret_scope_name}/openai-api-key}}"
        OPENAI_API_VERSION      = "{{secrets/${var.secret_scope_name}/openai-api-version}}"
        OPENAI_DEPLOYMENT_NAME  = "{{secrets/${var.secret_scope_name}/openai-deployment-name}}"
      }
    }

    traffic_config {
      routes {
        served_model_name  = var.served_model_name
        traffic_percentage = var.traffic_percentage
      }
    }
  }
}

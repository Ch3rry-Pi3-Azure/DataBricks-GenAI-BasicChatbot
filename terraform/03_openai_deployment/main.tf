terraform {
  required_version = ">= 1.5"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
  }
}

provider "azurerm" {
  features {}
}

data "azurerm_cognitive_account" "main" {
  name                = var.account_name
  resource_group_name = var.resource_group_name
}

resource "azurerm_cognitive_deployment" "main" {
  name                 = var.deployment_name
  cognitive_account_id = data.azurerm_cognitive_account.main.id

  model {
    format  = "OpenAI"
    name    = var.model_name
    version = var.model_version
  }

  scale {
    type     = var.scale_type
    capacity = var.deployment_capacity
  }
}

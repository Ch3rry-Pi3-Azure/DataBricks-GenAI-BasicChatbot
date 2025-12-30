terraform {
  required_version = ">= 1.5"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "azurerm" {
  features {}
}

data "azurerm_resource_group" "main" {
  name = var.resource_group_name
}

resource "random_pet" "openai" {
  length    = 2
  separator = ""
}

locals {
  account_name = var.account_name != null ? var.account_name : "${var.account_name_prefix}${random_pet.openai.id}"
}

resource "azurerm_cognitive_account" "main" {
  name                = local.account_name
  location            = coalesce(var.location, data.azurerm_resource_group.main.location)
  resource_group_name = data.azurerm_resource_group.main.name
  kind                = "OpenAI"
  sku_name            = var.sku_name

  custom_subdomain_name = local.account_name
  tags                  = var.tags
}

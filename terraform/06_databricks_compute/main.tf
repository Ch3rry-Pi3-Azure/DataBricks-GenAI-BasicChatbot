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

data "terraform_remote_state" "key_vault" {
  backend = "local"
  config = {
    path = "../05_key_vault/terraform.tfstate"
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

data "databricks_spark_version" "selected" {
  long_term_support = true
  ml                = false
}

data "databricks_node_type" "smallest" {
  local_disk = true
}

locals {
  resolved_spark_version = var.spark_version != null ? var.spark_version : data.databricks_spark_version.selected.id
  resolved_node_type_id  = var.node_type_id != null ? var.node_type_id : data.databricks_node_type.smallest.id
}

resource "databricks_secret_scope" "openai" {
  name         = var.secret_scope_name
  backend_type = "AZURE_KEYVAULT"

  keyvault_metadata {
    resource_id = data.terraform_remote_state.key_vault.outputs.key_vault_id
    dns_name    = data.terraform_remote_state.key_vault.outputs.key_vault_uri
  }
}

resource "databricks_cluster" "analytics" {
  cluster_name            = var.cluster_name
  spark_version           = local.resolved_spark_version
  node_type_id            = local.resolved_node_type_id
  autotermination_minutes = var.autotermination_minutes
  data_security_mode      = var.data_security_mode
  single_user_name        = var.single_user_name
  runtime_engine          = var.runtime_engine
  kind                    = var.kind
  is_single_node          = var.is_single_node
  use_ml_runtime          = var.use_ml_runtime

  num_workers = 0

  spark_conf = {
    "spark.databricks.cluster.profile" = "singleNode"
    "spark.master"                     = "local[*]"
  }

  library {
    pypi {
      package = var.openai_pypi_package
    }
  }

  depends_on = [databricks_secret_scope.openai]
}

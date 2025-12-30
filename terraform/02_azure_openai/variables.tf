variable "resource_group_name" {
  type        = string
  description = "Name of the existing resource group"
}

variable "location" {
  type        = string
  description = "Azure region for the OpenAI account (defaults to RG location if null)"
  default     = null
}

variable "account_name" {
  type        = string
  description = "Name of the Azure OpenAI account (must be globally unique). If null, a random suffix is appended."
  default     = null
}

variable "account_name_prefix" {
  type        = string
  description = "Prefix used to build the account name when account_name is null"
  default     = "aoaidbgenai"
}

variable "sku_name" {
  type        = string
  description = "Azure OpenAI SKU"
  default     = "S0"
}

variable "tags" {
  type        = map(string)
  description = "Tags applied to the Azure OpenAI account"
  default     = {}
}

variable "resource_group_name" {
  type        = string
  description = "Name of the existing resource group"
}

variable "location" {
  type        = string
  description = "Azure region for the Key Vault (defaults to RG location if null)"
  default     = null
}

variable "key_vault_name" {
  type        = string
  description = "Name of the Key Vault. If null, a random animal name is appended."
  default     = null
}

variable "key_vault_name_prefix" {
  type        = string
  description = "Prefix used to build the Key Vault name when key_vault_name is null"
  default     = "kvdbgenai"
}

variable "sku_name" {
  type        = string
  description = "Key Vault SKU (standard or premium)"
  default     = "standard"
}

variable "soft_delete_retention_days" {
  type        = number
  description = "Soft delete retention in days"
  default     = 7
}

variable "purge_protection_enabled" {
  type        = bool
  description = "Enable purge protection"
  default     = false
}

variable "tags" {
  type        = map(string)
  description = "Tags applied to the Key Vault"
  default     = {}
}

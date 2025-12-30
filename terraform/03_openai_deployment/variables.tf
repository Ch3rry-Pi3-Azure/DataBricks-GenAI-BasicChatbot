variable "resource_group_name" {
  type        = string
  description = "Name of the existing resource group"
}

variable "account_name" {
  type        = string
  description = "Name of the Azure OpenAI account"
}

variable "deployment_name" {
  type        = string
  description = "Name of the model deployment"
}

variable "model_name" {
  type        = string
  description = "Azure OpenAI model name"
  default     = "gpt-5-chat"
}

variable "model_version" {
  type        = string
  description = "Model version (must be supported in the chosen region)"
}

variable "scale_type" {
  type        = string
  description = "Deployment scale type"
  default     = "GlobalStandard"
}

variable "deployment_capacity" {
  type        = number
  description = "Deployment capacity units"
  default     = 1
}

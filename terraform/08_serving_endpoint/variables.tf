variable "resource_group_name" {
  type        = string
  description = "Name of the resource group containing the Databricks workspace"
}

variable "endpoint_name" {
  type        = string
  description = "Databricks serving endpoint name"
  default     = "basic-chatbot-endpoint"
}

variable "served_model_name" {
  type        = string
  description = "Name for the served model inside the endpoint"
  default     = "basic-chatbot"
}

variable "model_name" {
  type        = string
  description = "Registered MLflow model name (e.g. catalog.schema.model or model_name)"
  default     = "basic-chatbot"
}

variable "model_version" {
  type        = string
  description = "Model version to serve"
  default     = "1"
}

variable "secret_scope_name" {
  type        = string
  description = "Databricks secret scope name for serving environment variables"
  default     = "aoai-scope"
}

variable "workload_size" {
  type        = string
  description = "Serving workload size (Small, Medium, Large)"
  default     = "Small"
}

variable "scale_to_zero_enabled" {
  type        = bool
  description = "Enable scale-to-zero for the serving endpoint"
  default     = true
}

variable "traffic_percentage" {
  type        = number
  description = "Traffic percentage for the served model"
  default     = 100
}

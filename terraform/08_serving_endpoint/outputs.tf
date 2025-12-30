output "serving_endpoint_id" {
  value = databricks_model_serving.main.id
}

output "serving_endpoint_name" {
  value = databricks_model_serving.main.name
}

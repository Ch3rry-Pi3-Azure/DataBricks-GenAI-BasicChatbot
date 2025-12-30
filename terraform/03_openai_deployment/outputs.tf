output "deployment_name" {
  value = azurerm_cognitive_deployment.main.name
}

output "model_name" {
  value = azurerm_cognitive_deployment.main.model[0].name
}

output "model_version" {
  value = azurerm_cognitive_deployment.main.model[0].version
}

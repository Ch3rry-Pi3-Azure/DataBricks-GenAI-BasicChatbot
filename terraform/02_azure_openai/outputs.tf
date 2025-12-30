output "openai_account_id" {
  value = azurerm_cognitive_account.main.id
}

output "openai_account_name" {
  value = azurerm_cognitive_account.main.name
}

output "openai_endpoint" {
  value = azurerm_cognitive_account.main.endpoint
}

output "openai_primary_key" {
  value     = azurerm_cognitive_account.main.primary_access_key
  sensitive = true
}

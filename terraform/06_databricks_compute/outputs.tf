output "cluster_id" {
  value = databricks_cluster.analytics.id
}

output "cluster_name" {
  value = databricks_cluster.analytics.cluster_name
}

output "secret_scope_name" {
  value = databricks_secret_scope.openai.name
}

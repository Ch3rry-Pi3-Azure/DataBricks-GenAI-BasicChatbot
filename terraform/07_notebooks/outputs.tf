output "notebook_paths" {
  value = [for nb in databricks_notebook.notebooks : nb.path]
}

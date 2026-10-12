output "coolify_endpoint" {
  value = var.coolify_endpoint
}

output "server_uuid" {
  value = var.server_uuid
}

output "project_uuid" {
  value = coolify_project.this.uuid
}

output "dev_environment_uuid" {
  value = coolify_environment.dev.uuid
}

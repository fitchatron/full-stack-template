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

output "github_app_uuid" {
  value = var.github_app_uuid
}

output "git_repository" {
  value = var.git_repository
}

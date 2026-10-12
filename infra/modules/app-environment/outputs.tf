output "service_uuid" {
  description = "Coolify service UUID for the app stack. GitHub Actions deploys with this."
  value       = coolify_service.app.uuid
}

output "database_uuid" {
  description = "Coolify Postgres UUID (also its hostname on the Coolify network)."
  value       = coolify_database_postgresql.this.uuid
}

output "database_url" {
  description = "Internal connection string, as injected into the stack."
  value       = local.database_url
  sensitive   = true
}

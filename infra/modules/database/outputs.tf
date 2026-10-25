output "database_uuid" {
  description = "Coolify Postgres UUID (also its hostname on the Coolify network)."
  value       = coolify_database_postgresql.this.uuid
}

output "public_port" {
  description = "Port Postgres is published on, on the server: the far end of the SSH tunnel."
  value       = var.public_port
}

# The superuser's connection details. The roots use them only for Terraform's
# own admin connection; the app and runner get db-roles roles instead.
output "database_url" {
  description = "Internal connection string for the superuser."
  value       = local.database_url
  sensitive   = true
}

output "postgres_user" {
  value = var.postgres_user
}

output "postgres_db" {
  value = var.postgres_db
}

output "postgres_password" {
  value     = random_password.db.result
  sensitive = true
}

# Depend on this (not just the UUID) before logging in to the database.
output "ready" {
  value = terraform_data.ready.id
}

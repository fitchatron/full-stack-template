output "database_uuid" {
  description = "Coolify Postgres UUID (also its hostname on the Coolify network)."
  value       = coolify_database_postgresql.this.uuid
}

# The backend reads these four. Paste them into the app's env vars in Coolify.
output "database_url" {
  description = "Internal connection string for the app."
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

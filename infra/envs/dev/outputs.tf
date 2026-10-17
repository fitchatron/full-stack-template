# Values for the app's environment variables in Coolify.
# Read sensitive ones with: terraform output -raw <name>

output "database_uuid" {
  value = module.database.database_uuid
}

output "public_port" {
  value = module.database.public_port
}

output "database_url" {
  value     = module.database.database_url
  sensitive = true
}

output "postgres_user" {
  value = module.database.postgres_user
}

output "postgres_db" {
  value = module.database.postgres_db
}

output "postgres_password" {
  value     = module.database.postgres_password
  sensitive = true
}

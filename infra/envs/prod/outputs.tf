# Terraform already sets the app's env vars and the GitHub environment's
# secrets, using the backend and migrator roles. database_url, postgres_user and
# postgres_password below are the superuser's: for break-glass admin only,
# never for the app.
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

output "application_uuid" {
  value = module.app.application_uuid
}

# COOLIFY_WEBHOOK for this environment's GitHub Actions deploy job.
output "deploy_webhook" {
  value = "${local.shared.coolify_endpoint}/api/v1/deploy?uuid=${module.app.application_uuid}&force=false"
}
# Admin access for reviewing data: connect as readonly on public_port.
output "readonly_password" {
  value     = module.db_roles.readonly_password
  sensitive = true
}

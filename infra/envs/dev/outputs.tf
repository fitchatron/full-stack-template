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

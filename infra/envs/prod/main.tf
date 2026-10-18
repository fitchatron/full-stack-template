locals {
  shared = data.terraform_remote_state.shared.outputs
}

module "database" {
  source = "../../modules/database"

  app_name     = var.app_name
  env_name     = "prod"
  project_uuid = local.shared.project_uuid
  server_uuid  = local.shared.server_uuid

  # Coolify auto-creates "production" with the project; reference it by name.
  environment_name = "production"

  db_memory_limit = "1g"

  # Admin access from outside the server. Restrict this port to known IPs
  # in the firewall; the app itself uses the internal URL.
  is_public   = true
  public_port = 5434

  backup_schedule     = "0 2 * * *"
  backup_retain_local = 7

  # Off-site backups: create S3 storage in the Coolify UI, then set its UUID.
  # backup_s3_storage_uuid = "replace-with-s3-storage-uuid"
  # backup_retain_s3       = 30
}

module "app" {
  source = "../../modules/app"

  app_name         = var.app_name
  env_name         = "prod"
  project_uuid     = local.shared.project_uuid
  server_uuid      = local.shared.server_uuid
  environment_name = "production"

  github_app_uuid = local.shared.github_app_uuid
  git_repository  = local.shared.git_repository
  git_branch      = var.git_branch
  domain          = var.domain

  postgres_host     = module.database.database_uuid
  postgres_user     = module.database.postgres_user
  postgres_password = module.database.postgres_password
  postgres_db       = module.database.postgres_db

  app_env     = var.app_env
  app_secrets = var.app_secrets
}

locals {
  shared = data.terraform_remote_state.shared.outputs
}

module "app" {
  source = "../../modules/app-environment"

  app_name     = var.app_name
  env_name     = "prod"
  project_uuid = local.shared.project_uuid
  server_uuid  = local.shared.server_uuid

  # Coolify auto-creates "production" with the project; reference it by name.
  environment_name = "production"

  compose_file = "${path.module}/../../../compose.prod.yaml"
  domain       = var.domain

  # Placeholder until the first tagged release; Actions sets the real tag.
  initial_image_tag = "latest"

  app_env = {
    ENVIRONMENT = "prod"
    LOG_LEVEL   = "info"
  }
  app_secrets = var.app_secrets

  db_memory_limit = "1g"

  backup_schedule     = "0 2 * * *"
  backup_retain_local = 7

  # Off-site backups: create S3 storage in the Coolify UI, then set its UUID.
  # backup_s3_storage_uuid = "replace-with-s3-storage-uuid"
  # backup_retain_s3       = 30
}

locals {
  shared = data.terraform_remote_state.shared.outputs
}

module "app" {
  source = "../../modules/app-environment"

  app_name         = var.app_name
  env_name         = "dev"
  project_uuid     = local.shared.project_uuid
  server_uuid      = local.shared.server_uuid
  environment_uuid = local.shared.dev_environment_uuid

  compose_file      = "${path.module}/../../../compose.prod.yaml"
  domain            = var.domain
  initial_image_tag = "dev"

  app_env = {
    ENVIRONMENT = "dev"
    LOG_LEVEL   = "debug"
  }
  app_secrets = var.app_secrets

  db_memory_limit = "512m"

  # Dev data is disposable: a few local copies, nothing off-site.
  backup_schedule     = "0 3 * * *"
  backup_retain_local = 3
}

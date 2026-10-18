locals {
  shared = data.terraform_remote_state.shared.outputs
}

module "database" {
  source = "../../modules/database"

  app_name         = var.app_name
  env_name         = "dev"
  project_uuid     = local.shared.project_uuid
  server_uuid      = local.shared.server_uuid
  environment_uuid = local.shared.dev_environment_uuid

  db_memory_limit = "512m"

  # Admin access from outside the server. Restrict this port to known IPs
  # in the firewall; the app itself uses the internal URL.
  is_public   = true
  public_port = 5433

  # Dev data is disposable: a few local copies, nothing off-site.
  backup_schedule     = "0 3 * * *"
  backup_retain_local = 3
}

module "app" {
  source = "../../modules/app"

  app_name         = var.app_name
  env_name         = "dev"
  project_uuid     = local.shared.project_uuid
  server_uuid      = local.shared.server_uuid
  environment_uuid = local.shared.dev_environment_uuid

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

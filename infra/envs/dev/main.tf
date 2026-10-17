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

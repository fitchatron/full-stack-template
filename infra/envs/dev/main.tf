locals {
  shared = data.terraform_remote_state.shared.outputs

  # Local end of the SSH tunnel; by default the same number as the public
  # port.
  db_admin_port = coalesce(var.db_admin_port, module.database.public_port)
}

# This environment's own Docker network. Its database, app and runner join
# it instead of the server's shared `coolify` network, so the other
# environment (and anything else on the server) can't reach them, and
# compose service names can't resolve across environments. Every resource
# on the server then needs destination_uuid, or Coolify falls back to
# `coolify`. Renaming the network replaces everything on it.
resource "coolify_destination" "this" {
  server_uuid = local.shared.server_uuid
  network     = "${local.shared.project_id}-dev"
  name        = "${local.shared.project_id}-dev"
  type        = "standalone"
}

module "database" {
  source = "../../modules/database"

  admin_port = var.db_admin_port

  project_id       = local.shared.project_id
  env_name         = "dev"
  project_uuid     = local.shared.project_uuid
  server_uuid      = local.shared.server_uuid
  destination_uuid = coolify_destination.this.uuid
  environment_uuid = local.shared.dev_environment_uuid

  db_memory_limit = "512m"

  # Reached through an SSH tunnel only; block it in the VPS firewall.
  public_port = 5433

  # Dev data is disposable: a few local copies, nothing off-site.
  backup_schedule     = "0 3 * * *"
  backup_retain_local = 3
}

# Logs in as the superuser through an SSH tunnel to the public port, e.g.
#   ssh -N -L <public_port>:127.0.0.1:<public_port> <server>
# On a new environment Terraform configures this once the database exists,
# so one apply creates everything (open the tunnel first; it only connects
# through when used).
provider "postgresql" {
  host     = "127.0.0.1"
  port     = local.db_admin_port
  database = module.database.postgres_db
  username = module.database.postgres_user
  password = module.database.postgres_password
  # SSH encrypts the connection; Coolify can't enable Postgres TLS through
  # its API.
  sslmode         = "disable"
  connect_timeout = 15
}

module "db_roles" {
  source = "../../modules/db-roles"

  database  = module.database.postgres_db
  host      = module.database.database_uuid
  superuser = module.database.postgres_user

  # Postgres answers through the tunnel, not just created.
  depends_on = [module.database.ready]
}


module "app" {
  source = "../../modules/app"

  project_id       = local.shared.project_id
  app_name         = var.app_name
  env_name         = "dev"
  project_uuid     = local.shared.project_uuid
  server_uuid      = local.shared.server_uuid
  destination_uuid = coolify_destination.this.uuid
  environment_uuid = local.shared.dev_environment_uuid

  github_app_uuid = local.shared.github_app_uuid
  git_repository  = local.shared.git_repository
  git_branch      = var.git_branch
  domain          = var.domain

  postgres_host     = module.database.database_uuid
  postgres_user     = module.db_roles.backend.user
  postgres_password = module.db_roles.backend.password
  postgres_db       = module.database.postgres_db
  database_url      = module.db_roles.backend.database_url

  app_env     = var.app_env
  app_secrets = var.app_secrets
}

# Runs this environment's migrations (.github/workflows/deploy-db.yml).
module "runner" {
  source = "../../modules/runner"

  project_id       = local.shared.project_id
  env_name         = "dev"
  project_uuid     = local.shared.project_uuid
  server_uuid      = local.shared.server_uuid
  destination_uuid = coolify_destination.this.uuid
  docker_network   = coolify_destination.this.network
  environment_uuid = local.shared.dev_environment_uuid

  git_repository = local.shared.git_repository
  github_token   = var.github_runner_token
  # The second label matches the GitHub environment name.
  labels = ["coolify", "development"]

  job_env = {
    POSTGRES_HOST     = module.database.database_uuid
    POSTGRES_USER     = module.db_roles.migrator.user
    POSTGRES_PASSWORD = module.db_roles.migrator.password
    POSTGRES_DB       = module.database.postgres_db
    DATABASE_URL      = module.db_roles.migrator.database_url
  }
}

locals {
  shared = data.terraform_remote_state.shared.outputs
}

module "database" {
  source = "../../modules/database"

  project_id   = local.shared.project_id
  env_name     = "prod"
  project_uuid = local.shared.project_uuid
  server_uuid  = local.shared.server_uuid

  # Coolify auto-creates "production" with the project; reference it by name.
  environment_name = "production"

  db_memory_limit = "1g"

  # Admin and Terraform access, through an SSH tunnel only: block this port
  # from the internet in the VPS firewall. The app uses the internal URL.
  is_public   = true
  public_port = 5434

  backup_schedule     = "0 2 * * *"
  backup_retain_local = 7

  # Off-site backups: create S3 storage in the Coolify UI, then set its UUID.
  # backup_s3_storage_uuid = "replace-with-s3-storage-uuid"
  # backup_retain_s3       = 30
}

# Logs in as the superuser through an SSH tunnel to the public port, e.g.
#   ssh -N -L <public_port>:127.0.0.1:<public_port> <server>
# On a new environment Terraform configures this once the database exists,
# so one apply creates everything (open the tunnel first; it only connects
# through when used).
provider "postgresql" {
  host     = var.db_admin_host
  port     = coalesce(var.db_admin_port, module.database.public_port)
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

  database = module.database.postgres_db
  host     = module.database.database_uuid

  # Postgres is up, not just created.
  depends_on = [module.database.ready]
}


module "app" {
  source = "../../modules/app"

  project_id       = local.shared.project_id
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
  postgres_user     = module.db_roles.app.user
  postgres_password = module.db_roles.app.password
  postgres_db       = module.database.postgres_db
  database_url      = module.db_roles.app.database_url

  app_env     = var.app_env
  app_secrets = var.app_secrets
}

# Runs this environment's migrations (.github/workflows/deploy-db.yml).
module "runner" {
  source = "../../modules/runner"

  project_id       = local.shared.project_id
  env_name         = "prod"
  project_uuid     = local.shared.project_uuid
  server_uuid      = local.shared.server_uuid
  environment_name = "production"

  git_repository = local.shared.git_repository
  github_token   = var.github_runner_token
  # The second label matches the GitHub environment name.
  labels = ["coolify", "production"]

  job_env = {
    POSTGRES_HOST     = module.database.database_uuid
    POSTGRES_USER     = module.db_roles.migrator.user
    POSTGRES_PASSWORD = module.db_roles.migrator.password
    POSTGRES_DB       = module.database.postgres_db
    DATABASE_URL      = module.db_roles.migrator.database_url
  }
}

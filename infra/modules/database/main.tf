# One Postgres per environment, plus its backup schedule.
# The app itself is a git-based Docker Compose application created in the
# Coolify UI (see infra/README.md); Terraform only hands it the connection
# details via outputs.

locals {
  prefix = "${var.project_id}-${var.env_name}"

  # Coolify hands back postgres://user:pass@<host>:5432/db; swap the scheme
  # for the SQLAlchemy driver the backend uses.
  database_url = replace(
    coolify_database_postgresql.this.internal_db_url,
    "/^postgres(ql)?:\\/\\//",
    "${var.database_url_scheme}://",
  )
}

# Generated here so nobody ever types it. Lands in state, so treat the
# state file as a secret (see README).
resource "random_password" "db" {
  length  = 32
  special = false # avoids URL-encoding headaches in DATABASE_URL
}

resource "coolify_database_postgresql" "this" {
  name             = "${local.prefix}-db"
  description      = "Managed by Terraform"
  project_uuid     = var.project_uuid
  server_uuid      = var.server_uuid
  environment_uuid = var.environment_uuid
  environment_name = var.environment_name

  image             = var.postgres_image
  postgres_db       = var.postgres_db
  postgres_user     = var.postgres_user
  postgres_password = random_password.db.result

  # The app always connects over the Coolify network (database_url). Public
  # access is only for admins connecting from outside, e.g. with psql.
  is_public   = var.is_public
  public_port = var.is_public ? var.public_port : null

  instant_deploy = true
  limits_memory  = var.db_memory_limit

  lifecycle {
    # Applies to dev too. Comment out deliberately if you ever need to
    # tear an environment down.
    prevent_destroy = true
  }
}

# Coolify reports the database created before Postgres accepts connections.
# Anything that logs in to it (the db-roles module) waits on this. Only
# sleeps when the database is first created.
resource "time_sleep" "ready" {
  create_duration = var.ready_wait

  triggers = {
    database_uuid = coolify_database_postgresql.this.uuid
  }
}

resource "coolify_database_backup" "this" {
  count = var.backup_schedule == null ? 0 : 1

  database_uuid         = coolify_database_postgresql.this.uuid
  frequency             = var.backup_schedule
  enabled               = true
  retain_amount_locally = var.backup_retain_local

  save_s3          = var.backup_s3_storage_uuid != null
  s3_storage_uuid  = var.backup_s3_storage_uuid
  retain_amount_s3 = var.backup_s3_storage_uuid != null ? var.backup_retain_s3 : null
}

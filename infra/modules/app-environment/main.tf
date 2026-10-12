locals {
  prefix = "${var.app_name}-${var.env_name}"

  # Coolify hands back postgres://user:pass@<host>:5432/db; swap the scheme
  # so SQLAlchemy picks the async driver.
  database_url = replace(
    coolify_database_postgresql.this.internal_db_url,
    "/^postgres(ql)?:\\/\\//",
    "${var.database_url_scheme}://",
  )
}

# --- Postgres -----------------------------------------------------------------

# Generated here so nobody ever types or sees it. Lands in state, so treat the
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

  is_public      = false # only reachable from containers on the Coolify network
  instant_deploy = true
  limits_memory  = var.db_memory_limit

  lifecycle {
    # Applies to dev too. Comment out deliberately if you ever need to
    # tear an environment down.
    prevent_destroy = true
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

# --- App stack (nginx + frontend + backend) -----------------------------------

# A Coolify "service" running your compose file as-is. Images come from GHCR,
# so Coolify never builds; GitHub Actions bumps IMAGE_TAG and hits the webhook.
resource "coolify_service" "app" {
  name             = "${local.prefix}-app"
  description      = "Managed by Terraform"
  project_uuid     = var.project_uuid
  server_uuid      = var.server_uuid
  environment_uuid = var.environment_uuid
  environment_name = var.environment_name

  docker_compose_raw = file(var.compose_file)

  # Only nginx is public; Traefik (Coolify's proxy) routes the domain to it.
  urls = [
    {
      name = var.nginx_service_name
      url  = var.domain
    },
  ]

  # Needed so the stack can resolve the Postgres container by name.
  connect_to_docker_network = true

  # First deploy happens from GitHub Actions once images exist in GHCR.
  instant_deploy = false
}

# --- Env vars injected into the compose file's ${...} placeholders ------------

resource "coolify_environment_variable" "database_url" {
  service_uuid = coolify_service.app.uuid
  key          = "DATABASE_URL"
  value        = local.database_url
  is_literal   = true
}

resource "coolify_environment_variable" "image_tag" {
  service_uuid = coolify_service.app.uuid
  key          = "IMAGE_TAG"
  value        = var.initial_image_tag
  is_literal   = true

  lifecycle {
    # GitHub Actions updates this on every deploy. Without this, the next
    # terraform apply would roll prod back to initial_image_tag.
    ignore_changes = [value]
  }
}

resource "coolify_environment_variable" "app_env" {
  for_each = var.app_env

  service_uuid = coolify_service.app.uuid
  key          = each.key
  value        = each.value
  is_literal   = true
}

resource "coolify_environment_variable" "app_secrets" {
  # Keys aren't secret; values are. nonsensitive() on the key set lets for_each work.
  for_each = nonsensitive(toset(keys(var.app_secrets)))

  service_uuid = coolify_service.app.uuid
  key          = each.key
  value        = var.app_secrets[each.key]
  is_literal   = true
}

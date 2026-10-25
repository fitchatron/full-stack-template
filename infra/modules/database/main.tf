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

# Coolify reports a new database created before Postgres accepts
# connections, and anything that logs in to it straight after (the db-roles
# module) would fail. Poll Coolify until its healthcheck (pg_isready inside
# the container) passes: every 2s, failing after ready_timeout. Needs only
# curl. Runs once per database.
resource "terraform_data" "ready" {
  triggers_replace = [coolify_database_postgresql.this.uuid]

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]
    # The token falls back to the COOLIFY_TOKEN env var, like the provider.
    environment = merge(
      {
        COOLIFY_URL = trimsuffix(var.coolify_endpoint, "/")
        DB_UUID     = coolify_database_postgresql.this.uuid
        TIMEOUT     = tostring(var.ready_timeout)
      },
      var.coolify_token == null ? {} : { COOLIFY_TOKEN = var.coolify_token },
    )
    # Auth and lookup errors fail at once; anything else (Coolify
    # unreachable, image still pulling) is retried until the deadline, and
    # the last thing seen is reported.
    command = <<-EOT
      if [[ -z "$${COOLIFY_TOKEN:-}" ]]; then
        echo "No Coolify token: set coolify_token or the COOLIFY_TOKEN env var." >&2
        exit 1
      fi
      body=$(mktemp) err=$(mktemp)
      trap 'rm -f "$body" "$err"' EXIT
      deadline=$((SECONDS + TIMEOUT))
      last="no response yet"
      while true; do
        code=$(curl -sS -o "$body" -w '%%{http_code}' \
                 "$COOLIFY_URL/api/v1/databases/$DB_UUID" \
                 -H "Authorization: Bearer $COOLIFY_TOKEN" 2>"$err")
        case "$code" in
          200)
            status=$(grep -Eo '"status": ?"[^"]*"' "$body" | head -n1 | cut -d'"' -f4)
            [[ "$status" == "running:healthy" ]] && exit 0
            last="Coolify reports status '$${status:-unknown}'" ;;
          401|403)
            echo "Coolify rejected the token (HTTP $code) checking database $DB_UUID." >&2
            exit 1 ;;
          404)
            echo "Coolify has no database $DB_UUID (HTTP 404)." >&2
            exit 1 ;;
          000)
            last="couldn't reach $COOLIFY_URL: $(<"$err")" ;;
          *)
            last="Coolify returned HTTP $code" ;;
        esac
        if (( SECONDS >= deadline )); then
          echo "Database $DB_UUID not healthy after $${TIMEOUT}s: $last." >&2
          echo "A first create can take longer while the image pulls; raise ready_timeout or re-apply once it's up." >&2
          exit 1
        fi
        sleep 2
      done
    EOT
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

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

  # Published on the server so Terraform and admins can reach it through an
  # SSH tunnel. Block the port from the internet in the VPS provider's
  # firewall. The app always uses the internal URL (database_url).
  is_public   = true
  public_port = var.public_port

  instant_deploy = true
  limits_memory  = var.db_memory_limit

  lifecycle {
    # Applies to dev too. Comment out deliberately if you ever need to
    # tear an environment down.
    prevent_destroy = true
  }
}

# Coolify reports a new database created before Postgres accepts
# connections, and its public port (a separate proxy container) opens later
# still, so the db-roles module logging in straight after would fail. Check
# every 2s, until ready_timeout, that a real Postgres answers through the
# SSH tunnel: send its 8-byte SSLRequest and expect 'N' or 'S' back. A plain
# port check isn't enough, since the tunnel's local end accepts connections
# even when nothing answers behind it. Needs only bash. Runs once per
# database.
resource "terraform_data" "ready" {
  triggers_replace = [coolify_database_postgresql.this.uuid]

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]
    environment = {
      PGPORT      = tostring(coalesce(var.admin_port, var.public_port))
      PUBLIC_PORT = tostring(var.public_port)
      TIMEOUT     = tostring(var.ready_timeout)
    }
    command = <<-EOT
      pg_answers() {
        # braces keep 2>/dev/null to this line; on a bare exec it would
        # silence the whole script
        { exec 3<>"/dev/tcp/127.0.0.1/$PGPORT"; } 2>/dev/null || return 1
        printf '\x00\x00\x00\x08\x04\xd2\x16\x2f' >&3
        local reply=""
        IFS= read -r -t 2 -n 1 reply <&3 2>/dev/null
        exec 3<&- 3>&-
        [[ "$reply" == N || "$reply" == S ]]
      }
      deadline=$((SECONDS + TIMEOUT))
      until pg_answers; do
        if (( SECONDS >= deadline )); then
          echo "No Postgres answering on 127.0.0.1:$PGPORT after $${TIMEOUT}s." >&2
          echo "Is the SSH tunnel open? ssh -N -L $PGPORT:127.0.0.1:$PUBLIC_PORT <user>@<server>" >&2
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

# Least-privilege roles inside one environment's Postgres:
#   migrator - owns the schema; runs migrations (the runner)
#   app      - reads and writes rows, no DDL (the backend)
#   readonly - SELECT only, for admins reviewing data
# The superuser Coolify created stays for Terraform and break-glass use.
#
# Tables are created by migrator during migrations, so the default
# privileges below are what let app and readonly use tables that don't
# exist yet. Always run migrations as migrator: objects created by anyone
# else aren't covered.

locals {
  url_prefix = "${var.database_url_scheme}://"
  url_suffix = "@${var.host}:5432/${var.database}"

  app_table_privileges = ["SELECT", "INSERT", "UPDATE", "DELETE"]
  # identity/serial columns need USAGE to insert
  app_sequence_privileges = ["USAGE", "SELECT"]
}

# Generated here so nobody ever types them. special = false avoids
# URL-encoding in the connection strings.
resource "random_password" "this" {
  for_each = toset(["migrator", "app", "readonly"])

  length  = 32
  special = false
}

resource "postgresql_role" "migrator" {
  name     = "migrator"
  login    = true
  password = random_password.this["migrator"].result
}

resource "postgresql_role" "app" {
  name     = "app"
  login    = true
  password = random_password.this["app"].result
}

resource "postgresql_role" "readonly" {
  name     = "readonly"
  login    = true
  password = random_password.this["readonly"].result
}

# --- Grants --------------------------------------------------------------------
# Postgres rejects concurrent GRANTs on the same object ("tuple concurrently
# updated"), so every grant below depends on the one before it and they run
# one at a time.

resource "postgresql_grant" "connect_migrator" {
  database    = var.database
  role        = postgresql_role.migrator.name
  object_type = "database"
  privileges  = ["CONNECT"]
}

resource "postgresql_grant" "connect_app" {
  database    = var.database
  role        = postgresql_role.app.name
  object_type = "database"
  privileges  = ["CONNECT"]

  depends_on = [postgresql_grant.connect_migrator]
}

resource "postgresql_grant" "connect_readonly" {
  database    = var.database
  role        = postgresql_role.readonly.name
  object_type = "database"
  privileges  = ["CONNECT"]

  depends_on = [postgresql_grant.connect_app]
}

# Postgres 15+ denies CREATE in public to ordinary roles, so only migrator
# gets it.
resource "postgresql_grant" "schema_migrator" {
  database    = var.database
  schema      = "public"
  role        = postgresql_role.migrator.name
  object_type = "schema"
  privileges  = ["USAGE", "CREATE"]

  depends_on = [postgresql_grant.connect_readonly]
}

resource "postgresql_grant" "schema_app" {
  database    = var.database
  schema      = "public"
  role        = postgresql_role.app.name
  object_type = "schema"
  privileges  = ["USAGE"]

  depends_on = [postgresql_grant.schema_migrator]
}

resource "postgresql_grant" "schema_readonly" {
  database    = var.database
  schema      = "public"
  role        = postgresql_role.readonly.name
  object_type = "schema"
  privileges  = ["USAGE"]

  depends_on = [postgresql_grant.schema_app]
}

# Objects that already exist (e.g. alembic_version once migrator owns it).

resource "postgresql_grant" "tables_app" {
  database    = var.database
  schema      = "public"
  role        = postgresql_role.app.name
  object_type = "table"
  privileges  = local.app_table_privileges

  depends_on = [postgresql_grant.schema_readonly]
}

resource "postgresql_grant" "tables_readonly" {
  database    = var.database
  schema      = "public"
  role        = postgresql_role.readonly.name
  object_type = "table"
  privileges  = ["SELECT"]

  depends_on = [postgresql_grant.tables_app]
}

resource "postgresql_grant" "sequences_app" {
  database    = var.database
  schema      = "public"
  role        = postgresql_role.app.name
  object_type = "sequence"
  privileges  = local.app_sequence_privileges

  depends_on = [postgresql_grant.tables_readonly]
}

resource "postgresql_grant" "sequences_readonly" {
  database    = var.database
  schema      = "public"
  role        = postgresql_role.readonly.name
  object_type = "sequence"
  privileges  = ["SELECT"]

  depends_on = [postgresql_grant.sequences_app]
}

# Objects migrator creates later.

resource "postgresql_default_privileges" "tables_app" {
  database    = var.database
  schema      = "public"
  owner       = postgresql_role.migrator.name
  role        = postgresql_role.app.name
  object_type = "table"
  privileges  = local.app_table_privileges

  depends_on = [postgresql_grant.sequences_readonly]
}

resource "postgresql_default_privileges" "tables_readonly" {
  database    = var.database
  schema      = "public"
  owner       = postgresql_role.migrator.name
  role        = postgresql_role.readonly.name
  object_type = "table"
  privileges  = ["SELECT"]

  depends_on = [postgresql_default_privileges.tables_app]
}

resource "postgresql_default_privileges" "sequences_app" {
  database    = var.database
  schema      = "public"
  owner       = postgresql_role.migrator.name
  role        = postgresql_role.app.name
  object_type = "sequence"
  privileges  = local.app_sequence_privileges

  depends_on = [postgresql_default_privileges.tables_readonly]
}

resource "postgresql_default_privileges" "sequences_readonly" {
  database    = var.database
  schema      = "public"
  owner       = postgresql_role.migrator.name
  role        = postgresql_role.readonly.name
  object_type = "sequence"
  privileges  = ["SELECT"]

  depends_on = [postgresql_default_privileges.sequences_app]
}

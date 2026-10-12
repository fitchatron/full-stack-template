output "migrator" {
  description = "Credentials and internal connection string for running migrations."
  value = {
    user         = postgresql_role.migrator.name
    password     = random_password.this["migrator"].result
    database_url = "${local.url_prefix}${postgresql_role.migrator.name}:${random_password.this["migrator"].result}${local.url_suffix}"
  }
  sensitive = true
}

output "backend" {
  description = "Credentials and internal connection string for the backend."
  value = {
    user         = postgresql_role.backend.name
    password     = random_password.this["backend"].result
    database_url = "${local.url_prefix}${postgresql_role.backend.name}:${random_password.this["backend"].result}${local.url_suffix}"
  }
  sensitive = true
}

output "readonly_password" {
  value     = random_password.this["readonly"].result
  sensitive = true
}

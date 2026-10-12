variable "database" {
  description = "Database the roles are granted on."
  type        = string
}

variable "host" {
  description = "Postgres hostname on the environment's network (the database UUID), for the connection strings."
  type        = string
}

variable "superuser" {
  description = "Name of the superuser Coolify created (the database module's postgres_user), to check the role names don't collide with it."
  type        = string

  validation {
    condition     = !contains(local.roles, var.superuser)
    error_message = "The database superuser (${var.superuser}) can't share a name with a db-roles role (${join(", ", local.roles)})."
  }
}

variable "database_url_scheme" {
  description = "Scheme for the connection strings. The backend uses SQLAlchemy with psycopg 3."
  type        = string
  default     = "postgresql+psycopg"
}

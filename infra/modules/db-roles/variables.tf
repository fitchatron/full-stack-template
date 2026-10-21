variable "database" {
  description = "Database the roles are granted on."
  type        = string
}

variable "host" {
  description = "Postgres hostname on the Coolify network (the database UUID), for the connection strings."
  type        = string
}

variable "database_url_scheme" {
  description = "Scheme for the connection strings. The backend uses SQLAlchemy with psycopg 3."
  type        = string
  default     = "postgresql+psycopg"
}

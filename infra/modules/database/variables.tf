# --- Where it lives -----------------------------------------------------------

variable "project_id" {
  description = "Kebab-case project identifier (from the shared root), used as a prefix for Coolify resource names."
  type        = string
}

variable "env_name" {
  description = "Environment label used in resource names (dev, prod)."
  type        = string
}

variable "project_uuid" {
  description = "Coolify project UUID (from the shared root)."
  type        = string
}

variable "server_uuid" {
  description = "Coolify server UUID to deploy onto."
  type        = string
}

# Set exactly one of these. Prod uses the auto-created "production"
# environment by name; dev uses the UUID of the environment created in shared/.
variable "environment_uuid" {
  description = "Coolify environment UUID. Preferred: renames won't replace resources."
  type        = string
  default     = null
}

variable "environment_name" {
  description = "Coolify environment name. Use only for the built-in 'production' environment."
  type        = string
  default     = null
}

# --- Database -----------------------------------------------------------------

variable "postgres_image" {
  type    = string
  default = "postgres:18"
}

variable "postgres_db" {
  type    = string
  default = "app"
}

variable "postgres_user" {
  type    = string
  default = "app"
}

variable "db_memory_limit" {
  description = "Container memory limit for Postgres, e.g. 512m, 2g. null = unlimited."
  type        = string
  default     = null
}

variable "public_port" {
  description = "Port Coolify publishes Postgres on, on the server. Reached through an SSH tunnel; block it from the internet."
  type        = number
}

variable "admin_port" {
  description = "Local port of the SSH tunnel, for the readiness check. null means the same as public_port."
  type        = number
  default     = null
}

variable "ready_timeout" {
  description = "Seconds to keep checking (every 2s) that the new database answers through the SSH tunnel before failing."
  type        = number
  default     = 45
}

variable "database_url_scheme" {
  description = "Scheme for DATABASE_URL. The backend uses SQLAlchemy with psycopg 3."
  type        = string
  default     = "postgresql+psycopg"
}

# --- Backups ------------------------------------------------------------------

variable "backup_schedule" {
  description = "Cron for Postgres backups. null disables backups."
  type        = string
  default     = "0 2 * * *"
}

variable "backup_retain_local" {
  description = "Number of backup copies kept on the server."
  type        = number
  default     = 7
}

variable "backup_s3_storage_uuid" {
  description = "Coolify S3 storage UUID for off-site backups (create it in the Coolify UI). null = local only."
  type        = string
  default     = null
}

variable "backup_retain_s3" {
  type    = number
  default = 30
}

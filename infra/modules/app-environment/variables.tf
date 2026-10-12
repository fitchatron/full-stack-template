# --- Where it lives -----------------------------------------------------------

variable "app_name" {
  description = "Short app name, used as a prefix for Coolify resource names."
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

# --- App stack ----------------------------------------------------------------

variable "compose_file" {
  description = "Path to the compose file Coolify runs (images from GHCR, $${VAR} placeholders for env vars)."
  type        = string
}

variable "domain" {
  description = "Public URL for the nginx container, e.g. https://dev.example.com."
  type        = string
}

variable "nginx_service_name" {
  description = "Name of the nginx service in the compose file (the only one that gets a domain)."
  type        = string
  default     = "nginx"
}

variable "initial_image_tag" {
  description = "IMAGE_TAG set on first create only. After that, GitHub Actions owns it."
  type        = string
}

variable "app_env" {
  description = "Extra non-secret env vars for the stack (LOG_LEVEL, CORS origins, etc.)."
  type        = map(string)
  default     = {}
}

variable "app_secrets" {
  description = "Extra secret env vars for the stack (Entra client secret, API keys)."
  type        = map(string)
  default     = {}
  sensitive   = true
}

# --- Database -----------------------------------------------------------------

variable "postgres_image" {
  type    = string
  default = "postgres:17"
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

variable "database_url_scheme" {
  description = "Scheme for DATABASE_URL. SQLAlchemy async with asyncpg wants postgresql+asyncpg."
  type        = string
  default     = "postgresql+asyncpg"
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

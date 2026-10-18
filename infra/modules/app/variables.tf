# --- Where it lives -----------------------------------------------------------

variable "app_name" {
  description = "Short app name, used as a prefix for Coolify resource names and as PROJECT_NAME."
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

# Set exactly one of these, as for the database module.
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

# --- Source -------------------------------------------------------------------

variable "github_app_uuid" {
  description = "UUID of the GitHub App source in Coolify (Sources > the app). It must have access to the repo."
  type        = string
}

variable "git_repository" {
  description = "Repository as owner/name, e.g. fitchatron/full-stack-template."
  type        = string
}

variable "git_branch" {
  type    = string
  default = "main"
}

variable "domain" {
  description = "Public URL for the nginx service, e.g. https://app.example.com. Leave null until the first deploy has run."
  type        = string
  default     = null
}

# --- Env vars -----------------------------------------------------------------

variable "postgres_host" {
  description = "Postgres hostname on the Coolify network (the database UUID)."
  type        = string
}

variable "postgres_user" {
  type = string
}

variable "postgres_password" {
  type      = string
  sensitive = true
}

variable "postgres_db" {
  type = string
}

variable "app_env" {
  description = "Extra non-secret env vars, e.g. LOG_LEVEL. Overrides the defaults above on conflict."
  type        = map(string)
  default     = {}
}

variable "app_secrets" {
  description = "Extra secret env vars. Set in secrets.auto.tfvars."
  type        = map(string)
  default     = {}
  sensitive   = true
}

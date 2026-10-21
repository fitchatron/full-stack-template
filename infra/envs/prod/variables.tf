variable "app_name" {
  description = "Human-friendly app name, shown in the API docs and frontend (PROJECT_NAME). Resource names use project_id from shared."
  type        = string
}

variable "coolify_token" {
  description = "Coolify API token. Leave unset to use the COOLIFY_TOKEN env var instead."
  type        = string
  default     = null
  sensitive   = true
}

# CI moves production to each release tag; nobody commits to it.
variable "git_branch" {
  type    = string
  default = "production"
}

variable "domain" {
  description = "Public URL for the app, e.g. https://app.example.com. Leave unset until the first deploy (see README)."
  type        = string
  default     = null
}

variable "app_env" {
  description = "Extra non-secret env vars for the app, e.g. { LOG_LEVEL = \"DEBUG\" }."
  type        = map(string)
  default     = {}
}

variable "app_secrets" {
  description = "Extra secret env vars for the app. Set in secrets.auto.tfvars."
  type        = map(string)
  default     = {}
  sensitive   = true
}

variable "github_runner_token" {
  description = "Fine-grained PAT for this repo with Administration: read and write, used by the runner to register. Set in secrets.auto.tfvars."
  type        = string
  sensitive   = true
}

variable "db_admin_host" {
  description = "Where Terraform reaches Postgres to manage roles: the local end of the SSH tunnel."
  type        = string
  default     = "127.0.0.1"
}

variable "db_admin_port" {
  description = "Local port of the SSH tunnel. null uses the database's public port (tunnel the same port number through)."
  type        = number
  default     = null
}


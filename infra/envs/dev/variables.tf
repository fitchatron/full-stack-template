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

variable "git_branch" {
  type    = string
  default = "main"
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

variable "github_token" {
  description = "Fine-grained PAT for this repo with Administration, Environments, Secrets and Variables: read and write, used to manage the GitHub environment. Leave unset to use the GITHUB_TOKEN env var instead."
  type        = string
  default     = null
  sensitive   = true
}

variable "db_admin_port" {
  description = "Local port of the SSH tunnel Terraform reaches Postgres through. null means the same as the public port."
  type        = number
  default     = null
}


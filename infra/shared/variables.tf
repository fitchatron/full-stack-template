variable "coolify_endpoint" {
  description = "Coolify base URL, e.g. https://coolify.example.com"
  type        = string
}

variable "server_uuid" {
  description = "UUID of the Coolify server both environments run on (Servers > your server in the UI)."
  type        = string
}

variable "project_name" {
  type = string
}

variable "coolify_token" {
  description = "Coolify API token. Leave unset to use the COOLIFY_TOKEN env var instead."
  type        = string
  default     = null
  sensitive   = true
}
# The GitHub App is added once under Sources in the Coolify UI; both
# environments' apps clone through it.
variable "github_app_uuid" {
  description = "UUID of the GitHub App source in Coolify (Sources > the app)."
  type        = string
}

variable "git_repository" {
  description = "Repository the apps deploy from, as owner/name."
  type        = string
}

# --- Where it lives -----------------------------------------------------------

variable "app_name" {
  description = "Short app name, used as a prefix for Coolify resource and runner names."
  type        = string
}

variable "env_name" {
  description = "Environment label used in resource names (dev, prod)."
  type        = string
}

variable "project_uuid" {
  type = string
}

variable "server_uuid" {
  type = string
}

# Set exactly one of these, as for the database module.
variable "environment_uuid" {
  type    = string
  default = null
}

variable "environment_name" {
  type    = string
  default = null
}

# --- Runner -------------------------------------------------------------------

variable "git_repository" {
  description = "Repository the runner registers with, as owner/name."
  type        = string
}

variable "github_token" {
  description = "Fine-grained PAT for this repo with Administration: read and write. The runner uses it to register itself."
  type        = string
  sensitive   = true
}

variable "labels" {
  description = "Runner labels. Workflows select it with runs-on: [self-hosted, <labels>]."
  type        = list(string)
}

variable "runner_image" {
  description = "Runner image. Pin a specific tag from Docker Hub."
  type        = string
  default     = "myoung34/github-runner:2.338.0-ubuntu-noble"
}

variable "docker_network" {
  description = "Docker network the databases are on: the server's Coolify destination network."
  type        = string
  default     = "coolify"
}

variable "job_env" {
  description = "Env vars every job on this runner sees, e.g. the DB settings migrations need."
  type        = map(string)
  default     = {}
  sensitive   = true
}

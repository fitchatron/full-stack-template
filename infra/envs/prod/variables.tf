variable "app_name" {
  description = "Short app name, used as a prefix for Coolify resource names."
  type        = string
}

variable "coolify_token" {
  description = "Coolify API token. Leave unset to use the COOLIFY_TOKEN env var instead."
  type        = string
  default     = null
  sensitive   = true
}

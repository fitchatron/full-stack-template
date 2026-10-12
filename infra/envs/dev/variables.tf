variable "app_name" {
  type = string
}

variable "domain" {
  description = "Public URL for dev, e.g. https://dev.example.com"
  type        = string
}

variable "app_secrets" {
  description = "Secret env vars for the stack. Keep in secrets.auto.tfvars (gitignored) or TF_VAR_app_secrets."
  type        = map(string)
  default     = {}
  sensitive   = true
}

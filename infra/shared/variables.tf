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

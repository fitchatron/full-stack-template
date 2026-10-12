variable "repository" {
  description = "Repository name, without the owner (the provider sets the owner)."
  type        = string
}

variable "environment" {
  description = "GitHub environment name, as set-environment.yml outputs it (development, production)."
  type        = string
}

# Leave both pattern lists empty to let any branch or tag deploy.
variable "branch_patterns" {
  description = "Branches allowed to deploy to this environment, e.g. [\"main\"]."
  type        = list(string)
  default     = []
}

variable "tag_patterns" {
  description = "Tags allowed to deploy to this environment, e.g. [\"*.*.*\"]."
  type        = list(string)
  default     = []
}

variable "reviewer_user_ids" {
  description = "Numeric GitHub user IDs who must approve deploys (up to 6). Empty means no approval. Set them here, not in the UI, or every plan shows a diff."
  type        = list(number)
  default     = []
}

variable "secrets" {
  description = "Environment secrets, e.g. the migrator DB credentials."
  type        = map(string)
  default     = {}
  sensitive   = true
}

variable "variables" {
  description = "Non-secret environment variables."
  type        = map(string)
  default     = {}
}

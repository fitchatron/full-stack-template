# One Coolify project holding both environments. Coolify auto-creates a
# "production" environment with every project, so only dev is declared here.

resource "coolify_project" "this" {
  name        = var.project_name
  description = "Managed by Terraform"
}

resource "coolify_environment" "dev" {
  project_uuid = coolify_project.this.uuid
  name         = "dev"
  description  = "Deployed on push to main"

  # Deleting an environment cascade-deletes everything in it, database included.
  lifecycle {
    prevent_destroy = true
  }
}

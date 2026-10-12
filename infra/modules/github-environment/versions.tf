terraform {
  required_version = ">= 1.6"

  # Modules state a minimum; the roots pin the exact version.
  required_providers {
    github = {
      source  = "integrations/github"
      version = ">= 6.13.0"
    }
  }
}

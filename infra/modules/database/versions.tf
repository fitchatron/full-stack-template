terraform {
  required_version = ">= 1.6"

  # Modules state a minimum; the roots pin the exact version.
  required_providers {
    coolify = {
      source  = "coolify-terraform/coolify"
      version = ">= 0.1.26"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.6"
    }
  }
}

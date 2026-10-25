terraform {
  required_version = ">= 1.9" # validation referencing locals

  # Modules state a minimum; the roots pin the exact version.
  required_providers {
    postgresql = {
      source  = "cyrilgdn/postgresql"
      version = ">= 1.27.0"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.6"
    }
  }
}

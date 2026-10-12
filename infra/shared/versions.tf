terraform {
  required_version = ">= 1.6"

  required_providers {
    coolify = {
      source  = "coolify-terraform/coolify"
      version = "0.1.26" # pre-1.0: pin exactly, bump deliberately
    }
  }

  # Local state for now. When moving to S3/Blob, add a backend block here
  # and run: terraform init -migrate-state
}

# Token comes from the COOLIFY_TOKEN env var so it never sits in a file.
provider "coolify" {
  endpoint = var.coolify_endpoint
}

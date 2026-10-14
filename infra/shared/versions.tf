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

# Token comes from coolify_token in terraform.tfvars if provided. If not, it falls back to the COOLIFY_TOKEN env var.
provider "coolify" {
  endpoint = var.coolify_endpoint
  token    = var.coolify_token
}

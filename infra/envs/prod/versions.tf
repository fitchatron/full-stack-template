terraform {
  required_version = ">= 1.6"

  required_providers {
    coolify = {
      source  = "coolify-terraform/coolify"
      version = "0.1.26"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    postgresql = {
      source  = "cyrilgdn/postgresql"
      version = "1.27.0"
    }
    github = {
      source  = "integrations/github"
      version = "6.13.0"
    }
  }

  # Local state: envs/prod/terraform.tfstate. Separate from dev on purpose.
}

data "terraform_remote_state" "shared" {
  backend = "local"
  config = {
    path = "${path.module}/../../shared/terraform.tfstate"
  }
}

provider "coolify" {
  endpoint = data.terraform_remote_state.shared.outputs.coolify_endpoint
  token    = var.coolify_token
}

provider "github" {
  owner = local.github_owner
  token = var.github_token
}

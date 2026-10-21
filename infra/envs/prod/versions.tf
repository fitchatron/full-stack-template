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
    time = {
      source  = "hashicorp/time"
      version = "0.14.2"
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
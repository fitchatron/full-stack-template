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
  }

  # Local state: envs/dev/terraform.tfstate. Separate from prod on purpose.
}

data "terraform_remote_state" "shared" {
  backend = "local"
  config = {
    path = "${path.module}/../../shared/terraform.tfstate"
  }
}

# Token from the COOLIFY_TOKEN env var. Needs deploy + read:sensitive
# permissions (read:sensitive so compose and DB URLs read back without diffs).
provider "coolify" {
  endpoint = data.terraform_remote_state.shared.outputs.coolify_endpoint
}

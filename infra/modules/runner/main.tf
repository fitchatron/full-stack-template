# A self-hosted GitHub Actions runner for one environment, running as a
# Coolify service on the environment's network. Jobs on it reach Postgres by
# its internal hostname and get the environment's DB settings from the
# runner's env, so GitHub never holds DB credentials.

locals {
  prefix = "${var.project_id}-${var.env_name}"

  # Coolify turns each ${VAR} in the compose file into a service env var,
  # which coolify_envs_bulk below fills in.
  passthrough = concat(["ACCESS_TOKEN"], nonsensitive(keys(var.job_env)))

  compose = yamlencode({
    services = {
      runner = {
        image   = var.runner_image
        restart = "always"
        environment = merge(
          {
            REPO_URL             = "https://github.com/${var.git_repository}"
            RUNNER_SCOPE         = "repo"
            RUNNER_NAME_PREFIX   = local.prefix
            RUNNER_WORKDIR       = "/_work"
            RANDOM_RUNNER_SUFFIX = "true"
            LABELS               = join(",", var.labels)
            # Re-registers with a clean workspace after every job.
            EPHEMERAL           = "true"
            DISABLE_AUTO_UPDATE = "true"
            RUN_AS_ROOT         = "false"
          },
          { for k in local.passthrough : k => "$${${k}}" },
        )
        # Lets jobs reach Postgres by name. Coolify's API rejects
        # connect_to_docker_network on services, so join it here instead.
        networks = [var.docker_network]
      }
    }
    networks = {
      (var.docker_network) = { external = true }
    }
  })
}

resource "coolify_service" "this" {
  name             = "${local.prefix}-runner"
  description      = "Managed by Terraform"
  project_uuid     = var.project_uuid
  server_uuid      = var.server_uuid
  environment_uuid = var.environment_uuid
  environment_name = var.environment_name
  destination_uuid = var.destination_uuid

  docker_compose_raw = local.compose

  # Started below, once its env vars are set.
  instant_deploy = false
}

resource "coolify_envs_bulk" "this" {
  resource_type = "service"
  resource_uuid = coolify_service.this.uuid
  variables     = merge(var.job_env, { ACCESS_TOKEN = var.github_token })
}

# Env changes only reach the container on a restart.
resource "coolify_resource_action" "restart" {
  action        = "restart"
  resource_type = "service"
  resource_uuid = coolify_service.this.uuid

  triggers = {
    compose = sha256(local.compose)
    env     = sha256(jsonencode(coolify_envs_bulk.this.variables))
  }
}

# A self-hosted GitHub Actions runner for one environment, running as a
# Coolify service on the environment's network, so jobs on it reach Postgres
# by its internal hostname. It holds no DB credentials: any job can pick a
# runner by its labels, so deploy jobs get them from the GitHub environment
# (modules/github-environment), which gates who can read them.

locals {
  prefix = "${var.project_id}-${var.env_name}"

  compose = yamlencode({
    services = {
      runner = {
        image   = var.runner_image
        restart = "always"
        # The image puts the runner user in a passwordless sudo group, so a
        # job could read the PAT back from PID 1's environment. Drop it
        # before the image's own entrypoint runs (it is root until it hands
        # over to the runner user). Overriding the entrypoint clears the
        # image's CMD, so that is repeated too.
        entrypoint = [
          "/bin/bash", "-c",
          "{ ! id -nG runner | grep -qw sudo || gpasswd -d runner sudo; } && exec /entrypoint.sh ./bin/Runner.Listener run --startuptype service",
        ]
        environment = {
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
          # Clears ACCESS_TOKEN and the other settings from the env the
          # runner, and so every job, inherits. The container's own env
          # keeps them, so each restart can register again.
          UNSET_CONFIG_VARS = "true"
          # Deregistering on exit needs the cleared token. GitHub removes
          # an ephemeral runner after its job anyway.
          DISABLE_AUTOMATIC_DEREGISTRATION = "true"
          # Coolify turns ${ACCESS_TOKEN} into a service env var, which
          # coolify_envs_bulk below fills in.
          ACCESS_TOKEN = "$${ACCESS_TOKEN}"
        }
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
  variables     = { ACCESS_TOKEN = var.github_token }
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

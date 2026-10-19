# The git-based Docker Compose app for one environment, plus its env vars.
# Coolify reads compose.prod.yml from the repo on every deploy; this only
# manages the Coolify resource around it.

locals {
  prefix = "${var.project_id}-${var.env_name}"
}

# Generated here so nobody ever types it. Lands in state, so treat the
# state file as a secret (see README).
resource "random_password" "secret_key" {
  length  = 64
  special = false
}

resource "coolify_application_github_app" "this" {
  name             = "${local.prefix}-app"
  description      = "Managed by Terraform"
  project_uuid     = var.project_uuid
  server_uuid      = var.server_uuid
  environment_uuid = var.environment_uuid
  environment_name = var.environment_name

  github_app_uuid = var.github_app_uuid
  git_repository  = var.git_repository
  git_branch      = var.git_branch

  build_pack              = "dockercompose"
  base_directory          = "/"
  docker_compose_location = "/compose.prod.yml"
  ports_exposes           = "80"

  # Coolify rejects compose domains until a deploy has loaded the compose
  # file, so this stays unset on the first apply (see README).
  docker_compose_domains = var.domain == null ? null : jsonencode([
    { name = "nginx", domain = var.domain },
  ])

  # "Connect To Predefined Network": lets the stack reach Postgres by name.
  connect_to_docker_network = true

  # CI deploys through the webhook after pushing images. Auto deploy would
  # redeploy the previous images on every push.
  is_auto_deploy_enabled = false
  instant_deploy         = false
}

resource "coolify_envs_bulk" "this" {
  resource_type = "application"
  resource_uuid = coolify_application_github_app.this.uuid

  variables = merge(
    {
      PROJECT_NAME      = var.app_name
      SECRET_KEY        = random_password.secret_key.result
      POSTGRES_HOST     = var.postgres_host
      POSTGRES_USER     = var.postgres_user
      POSTGRES_PASSWORD = var.postgres_password
      POSTGRES_DB       = var.postgres_db
      DATABASE_URL      = var.database_url
    },
    var.app_env,
    var.app_secrets,
  )
}

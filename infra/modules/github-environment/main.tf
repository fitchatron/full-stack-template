# The GitHub environment for one Coolify environment, plus the secrets and
# variables its deploy jobs read. GitHub only hands environment secrets to
# jobs that declare `environment:` and pass its deployment rules, so this is
# where the migrator credentials live, not on the runner: any job can land
# on a self-hosted runner by its labels, gated or not.

resource "github_repository_environment" "this" {
  repository  = var.repository
  environment = var.environment

  dynamic "reviewers" {
    for_each = length(var.reviewer_user_ids) > 0 ? [1] : []
    content {
      users = var.reviewer_user_ids
    }
  }

  # Only the refs below may deploy here (and so read the secrets).
  deployment_branch_policy {
    protected_branches     = false
    custom_branch_policies = true
  }
}

resource "github_repository_environment_deployment_policy" "branch" {
  for_each = toset(var.branch_patterns)

  repository     = var.repository
  environment    = github_repository_environment.this.environment
  branch_pattern = each.value
}

resource "github_repository_environment_deployment_policy" "tag" {
  for_each = toset(var.tag_patterns)

  repository  = var.repository
  environment = github_repository_environment.this.environment
  tag_pattern = each.value
}

resource "github_actions_environment_secret" "this" {
  for_each = nonsensitive(toset(keys(var.secrets)))

  repository  = var.repository
  environment = github_repository_environment.this.environment
  secret_name = each.value
  value       = var.secrets[each.value]
}

resource "github_actions_environment_variable" "this" {
  for_each = var.variables

  repository    = var.repository
  environment   = github_repository_environment.this.environment
  variable_name = each.key
  value         = each.value
}

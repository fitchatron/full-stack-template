output "service_uuid" {
  description = "Add to GitHub as the prod COOLIFY_SERVICE_UUID variable."
  value       = module.app.service_uuid
}

output "deploy_webhook" {
  description = "Add to GitHub as the prod COOLIFY_WEBHOOK secret."
  value       = "${local.shared.coolify_endpoint}/api/v1/deploy?uuid=${module.app.service_uuid}"
}

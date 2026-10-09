output "tf_state_bucket" {
  description = "Set this as the GitHub Actions variable TF_STATE_BUCKET."
  value       = aws_s3_bucket.tf_state.bucket
}

output "tf_lock_table" {
  description = "Set this as the GitHub Actions variable TF_LOCK_TABLE."
  value       = aws_dynamodb_table.tf_lock.name
}

output "plan_role_arn" {
  description = "Set this as the GitHub Actions secret AWS_PLAN_ROLE_ARN."
  value       = aws_iam_role.plan.arn
}

output "deploy_role_arn" {
  description = "Set this as the GitHub Actions secret AWS_DEPLOY_ROLE_ARN."
  value       = aws_iam_role.deploy.arn
}

output "github_oidc_provider_arn" {
  description = "OIDC provider used by both GitHub Actions roles."
  value       = aws_iam_openid_connect_provider.github.arn
}

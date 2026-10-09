output "app_domain" {
  description = "Browser URL for the frontend."
  value       = local.cors_origin
}

output "api_domain" {
  description = "Public API base URL. Pass this as VITE_API_URL when building the frontend image."
  value       = local.api_url
}

output "private_backend_domain" {
  description = "Private backend URL used by the AI worker."
  value       = local.backend_url
}

output "sqs_queue_url" {
  description = "Document processing queue URL."
  value       = aws_sqs_queue.documents.url
}

output "s3_bucket_name" {
  description = "Private upload bucket."
  value       = aws_s3_bucket.uploads.bucket
}

output "ecr_frontend_url" {
  description = "ECR repository for the frontend image."
  value       = aws_ecr_repository.frontend.repository_url
}

output "ecr_backend_url" {
  description = "ECR repository for the backend image."
  value       = aws_ecr_repository.backend.repository_url
}

output "ecr_ai_url" {
  description = "ECR repository for the AI worker image."
  value       = aws_ecr_repository.ai.repository_url
}

output "public_alb_dns_name" {
  description = "Load balancer address. Point app.<domain> and api.<domain> at this to test before the domain is delegated."
  value       = aws_lb.public.dns_name
}

output "public_zone_name_servers" {
  description = "Delegate the public domain to these name servers before the app hostname resolves."
  value       = aws_route53_zone.public.name_servers
}

output "ecs_cluster_name" {
  description = "ECS cluster name used by the deploy workflow force-new-deployment step."
  value       = aws_ecs_cluster.main.name
}

output "ecs_frontend_service_name" {
  description = "Frontend ECS service name."
  value       = aws_ecs_service.frontend.name
}

output "ecs_backend_service_name" {
  description = "Backend ECS service name."
  value       = aws_ecs_service.backend.name
}

output "ecs_ai_service_name" {
  description = "AI worker ECS service name."
  value       = aws_ecs_service.ai.name
}

variable "aws_region" {
  description = "Region for the state bucket, lock table, and IAM roles."
  type        = string
  default     = "us-east-1"
}

variable "name_prefix" {
  description = "Short prefix. Must match the main stack so IAM name filters stay aligned."
  type        = string
  default     = "cda"
}

variable "github_org" {
  description = "GitHub org or user that owns the repository."
  type        = string
  default     = "haseebpvt"
}

variable "github_repo" {
  description = "Repository name."
  type        = string
  default     = "ai-customer-document-assistant"
}

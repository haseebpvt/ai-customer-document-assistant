variable "aws_region" {
  description = "Region for all resources. Defaults to us-east-1 so Bedrock is available."
  type        = string
  default     = "us-east-1"
}

variable "public_domain" {
  description = "Public DNS zone. App and API are app.<domain> and api.<domain>."
  type        = string
  default     = "cda.example.com"
}

variable "name_prefix" {
  description = "Short prefix for resource names."
  type        = string
  default     = "cda"
}

variable "bedrock_model_id" {
  description = "Vision model id for image text extraction."
  type        = string
  default     = "amazon.nova-lite-v1:0"
}

variable "bedrock_classify_model_id" {
  description = "Smaller text model id for classify, extract, and summary."
  type        = string
  default     = "amazon.nova-micro-v1:0"
}

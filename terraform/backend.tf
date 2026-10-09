# Bucket and lock table come from terraform/bootstrap and are passed at init time.
# Local validate uses: terraform init -backend=false
terraform {
  backend "s3" {
    key = "ai-customer-document-assistant/terraform.tfstate"
  }
}

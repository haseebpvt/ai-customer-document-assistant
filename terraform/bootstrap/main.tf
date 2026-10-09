data "aws_caller_identity" "current" {}

locals {
  github_sub_plan   = "repo:${var.github_org}/${var.github_repo}:pull_request"
  github_sub_deploy = "repo:${var.github_org}/${var.github_repo}:ref:refs/heads/main"
}

# Local state only. This stack creates the remote backend the main stack needs.
resource "aws_s3_bucket" "tf_state" {
  bucket_prefix = "${var.name_prefix}-tfstate-"

  tags = {
    Name = "${var.name_prefix}-tfstate"
  }
}

resource "aws_s3_bucket_versioning" "tf_state" {
  bucket = aws_s3_bucket.tf_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tf_state" {
  bucket = aws_s3_bucket.tf_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "tf_state" {
  bucket = aws_s3_bucket.tf_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_dynamodb_table" "tf_lock" {
  name         = "${var.name_prefix}-tf-lock"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name = "${var.name_prefix}-tf-lock"
  }
}

resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["ffffffffffffffffffffffffffffffffffffffff"]
}

data "aws_iam_policy_document" "plan_assume" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = [local.github_sub_plan]
    }
  }
}

resource "aws_iam_role" "plan" {
  # Outside the cda-* pattern so the deploy role cannot edit this trust policy.
  name               = "gha-${var.name_prefix}-plan"
  assume_role_policy = data.aws_iam_policy_document.plan_assume.json
}

# Plan refreshes state and reads existing resources. It cannot create or update them.
resource "aws_iam_role_policy_attachment" "plan_readonly" {
  role       = aws_iam_role.plan.name
  policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
}

data "aws_iam_policy_document" "plan_state" {
  statement {
    sid = "StateBucket"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket",
    ]
    resources = [
      aws_s3_bucket.tf_state.arn,
      "${aws_s3_bucket.tf_state.arn}/*",
    ]
  }

  statement {
    sid = "StateLock"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:DeleteItem",
      "dynamodb:DescribeTable",
    ]
    resources = [aws_dynamodb_table.tf_lock.arn]
  }

  # Plan refreshes the DATABASE_URL secret. Create stays on the deploy role.
  statement {
    sid       = "ReadDatabaseSecret"
    actions   = ["secretsmanager:GetSecretValue"]
    resources = ["arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:${var.name_prefix}-database-url-*"]
  }
}

resource "aws_iam_role_policy" "plan_state" {
  name   = "terraform-state-and-lock"
  role   = aws_iam_role.plan.id
  policy = data.aws_iam_policy_document.plan_state.json
}

data "aws_iam_policy_document" "deploy_assume" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = [local.github_sub_deploy]
    }
  }
}

resource "aws_iam_role" "deploy" {
  # Outside the cda-* pattern so this role cannot rewrite its own trust policy.
  name               = "gha-${var.name_prefix}-deploy"
  assume_role_policy = data.aws_iam_policy_document.deploy_assume.json
}

# Not AdministratorAccess. Covers the services the main stack creates, plus ECR push and ECS rollout.
data "aws_iam_policy_document" "deploy" {
  statement {
    sid = "StateBucket"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket",
      "s3:GetBucket*",
      "s3:PutBucket*",
      "s3:CreateBucket",
      "s3:DeleteBucket",
      "s3:PutEncryptionConfiguration",
      "s3:GetEncryptionConfiguration",
      "s3:PutPublicAccessBlock",
      "s3:GetPublicAccessBlock",
      "s3:PutBucketVersioning",
      "s3:GetBucketVersioning",
    ]
    resources = ["*"]
  }

  statement {
    sid = "StateLock"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:DeleteItem",
      "dynamodb:DescribeTable",
    ]
    resources = [aws_dynamodb_table.tf_lock.arn]
  }

  statement {
    sid = "Network"
    actions = [
      "ec2:*",
      "elasticloadbalancing:*",
    ]
    resources = ["*"]
  }

  statement {
    sid = "Dns"
    actions = [
      "route53:*",
    ]
    resources = ["*"]
  }

  statement {
    sid = "Compute"
    actions = [
      "ecs:*",
      "ecr:*",
      "logs:*",
      "application-autoscaling:*",
      "cloudwatch:PutMetricAlarm",
      "cloudwatch:DescribeAlarms",
      "cloudwatch:DeleteAlarms",
    ]
    resources = ["*"]
  }

  statement {
    sid = "Data"
    actions = [
      "sqs:*",
      "rds:*",
      "secretsmanager:*",
    ]
    resources = ["*"]
  }

  # Task and execution roles are named with the prefix. Bootstrap roles stay outside this apply.
  statement {
    sid = "IamRoles"
    actions = [
      "iam:CreateRole",
      "iam:DeleteRole",
      "iam:GetRole",
      "iam:TagRole",
      "iam:UntagRole",
      "iam:UpdateAssumeRolePolicy",
      "iam:PutRolePolicy",
      "iam:GetRolePolicy",
      "iam:DeleteRolePolicy",
      "iam:AttachRolePolicy",
      "iam:DetachRolePolicy",
      "iam:ListAttachedRolePolicies",
      "iam:ListRolePolicies",
      "iam:PassRole",
    ]
    resources = [
      "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.name_prefix}-*",
    ]
  }

  statement {
    sid = "IamServiceLinked"
    actions = [
      "iam:CreateServiceLinkedRole",
    ]
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "iam:AWSServiceName"
      values = [
        "ecs.amazonaws.com",
        "ecs.application-autoscaling.amazonaws.com",
        "elasticloadbalancing.amazonaws.com",
        "rds.amazonaws.com",
      ]
    }
  }
}

resource "aws_iam_role_policy" "deploy" {
  name   = "main-stack-deploy"
  role   = aws_iam_role.deploy.id
  policy = data.aws_iam_policy_document.deploy.json
}

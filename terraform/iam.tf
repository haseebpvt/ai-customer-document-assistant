data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "ecs_assume" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

# Shared execution role: pull images and write logs.
resource "aws_iam_role" "ecs_execution" {
  name               = "${var.name_prefix}-ecs-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Only the backend execution role reads the database secret into the task.
resource "aws_iam_role" "backend_execution" {
  name               = "${var.name_prefix}-backend-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json
}

resource "aws_iam_role_policy_attachment" "backend_execution_base" {
  role       = aws_iam_role.backend_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

data "aws_iam_policy_document" "backend_execution_secret" {
  statement {
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [aws_secretsmanager_secret.database_url.arn]
  }
}

resource "aws_iam_role_policy" "backend_execution_secret" {
  name   = "read-database-url"
  role   = aws_iam_role.backend_execution.id
  policy = data.aws_iam_policy_document.backend_execution_secret.json
}

# Frontend task role has no AWS API permissions.
resource "aws_iam_role" "frontend_task" {
  name               = "${var.name_prefix}-frontend-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json
}

# Backend task role: boto3 PutObject and SendMessage.
resource "aws_iam_role" "backend_task" {
  name               = "${var.name_prefix}-backend-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json
}

data "aws_iam_policy_document" "backend_task" {
  statement {
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.uploads.arn}/*"]
  }

  statement {
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.documents.arn]
  }
}

resource "aws_iam_role_policy" "backend_task" {
  name   = "backend-upload-and-queue"
  role   = aws_iam_role.backend_task.id
  policy = data.aws_iam_policy_document.backend_task.json
}

# AI task role: GetObject, receive and delete messages, Bedrock. No database.
resource "aws_iam_role" "ai_task" {
  name               = "${var.name_prefix}-ai-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json
}

data "aws_iam_policy_document" "ai_task" {
  statement {
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.uploads.arn}/*"]
  }

  statement {
    actions = [
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:ChangeMessageVisibility",
      "sqs:GetQueueAttributes",
    ]
    resources = [aws_sqs_queue.documents.arn]
  }

  # Model ids are env vars, so IAM is not pinned to one model.
  statement {
    # The Converse API is authorized by bedrock:InvokeModel.
    actions = ["bedrock:InvokeModel"]
    resources = [
      "arn:aws:bedrock:${var.aws_region}::foundation-model/*",
      "arn:aws:bedrock:${var.aws_region}:${data.aws_caller_identity.current.account_id}:inference-profile/*",
    ]
  }
}

resource "aws_iam_role_policy" "ai_task" {
  name   = "ai-process-documents"
  role   = aws_iam_role.ai_task.id
  policy = data.aws_iam_policy_document.ai_task.json
}

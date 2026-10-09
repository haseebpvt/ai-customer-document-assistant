resource "aws_s3_bucket" "uploads" {
  bucket_prefix = "${var.name_prefix}-uploads-"

  tags = {
    Name = "${var.name_prefix}-uploads"
  }
}

resource "aws_s3_bucket_public_access_block" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_sqs_queue" "dead_letter" {
  name = "${var.name_prefix}-documents-dlq"

  tags = {
    Name = "${var.name_prefix}-documents-dlq"
  }
}

# Longer than one graph run, including Bedrock retries. Short enough that a stopped task is retried soon.
resource "aws_sqs_queue" "documents" {
  name                       = "${var.name_prefix}-documents"
  visibility_timeout_seconds = 300
  receive_wait_time_seconds  = 20

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dead_letter.arn
    maxReceiveCount     = 3
  })

  tags = {
    Name = "${var.name_prefix}-documents"
  }
}

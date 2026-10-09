resource "aws_security_group" "public_alb" {
  name        = "${var.name_prefix}-public-alb"
  description = "Public load balancer for app and api hostnames"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${var.name_prefix}-public-alb"
  }
}

resource "aws_vpc_security_group_ingress_rule" "public_alb_http" {
  for_each = toset(var.allowed_cidrs)

  security_group_id = aws_security_group.public_alb.id
  description       = "HTTP from an allowed network"
  from_port         = 80
  to_port           = 80
  ip_protocol       = "tcp"
  cidr_ipv4         = each.value
}

resource "aws_vpc_security_group_egress_rule" "public_alb_all" {
  security_group_id = aws_security_group.public_alb.id
  description       = "Forward to tasks"
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_security_group" "internal_alb" {
  name        = "${var.name_prefix}-internal-alb"
  description = "Internal load balancer for worker PATCH calls"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${var.name_prefix}-internal-alb"
  }
}

resource "aws_vpc_security_group_ingress_rule" "internal_alb_from_ai" {
  security_group_id            = aws_security_group.internal_alb.id
  description                  = "HTTP from the AI worker only"
  from_port                    = 80
  to_port                      = 80
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.ai.id
}

resource "aws_vpc_security_group_egress_rule" "internal_alb_all" {
  security_group_id = aws_security_group.internal_alb.id
  description       = "Forward to backend tasks"
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_security_group" "frontend" {
  name        = "${var.name_prefix}-frontend"
  description = "Frontend nginx tasks"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${var.name_prefix}-frontend"
  }
}

resource "aws_vpc_security_group_ingress_rule" "frontend_from_public_alb" {
  security_group_id            = aws_security_group.frontend.id
  description                  = "HTTP from the public load balancer"
  from_port                    = 80
  to_port                      = 80
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.public_alb.id
}

resource "aws_vpc_security_group_egress_rule" "frontend_https" {
  security_group_id = aws_security_group.frontend.id
  description       = "HTTPS for ECR and CloudWatch"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_security_group" "backend" {
  name        = "${var.name_prefix}-backend"
  description = "Backend API tasks"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${var.name_prefix}-backend"
  }
}

resource "aws_vpc_security_group_ingress_rule" "backend_from_public_alb" {
  security_group_id            = aws_security_group.backend.id
  description                  = "HTTP from the public load balancer"
  from_port                    = 8000
  to_port                      = 8000
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.public_alb.id
}

resource "aws_vpc_security_group_ingress_rule" "backend_from_internal_alb" {
  security_group_id            = aws_security_group.backend.id
  description                  = "HTTP from the internal load balancer"
  from_port                    = 8000
  to_port                      = 8000
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.internal_alb.id
}

resource "aws_vpc_security_group_egress_rule" "backend_https" {
  security_group_id = aws_security_group.backend.id
  description       = "HTTPS for S3, SQS, Secrets Manager, ECR, CloudWatch"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_vpc_security_group_egress_rule" "backend_to_rds" {
  security_group_id            = aws_security_group.backend.id
  description                  = "Postgres to RDS"
  from_port                    = 5432
  to_port                      = 5432
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.rds.id
}

resource "aws_security_group" "ai" {
  name        = "${var.name_prefix}-ai"
  description = "AI worker tasks. No inbound. No public IP."
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${var.name_prefix}-ai"
  }
}

resource "aws_vpc_security_group_egress_rule" "ai_https" {
  security_group_id = aws_security_group.ai.id
  description       = "HTTPS for S3, SQS, Bedrock, ECR, CloudWatch"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_vpc_security_group_egress_rule" "ai_to_internal_alb" {
  security_group_id            = aws_security_group.ai.id
  description                  = "HTTP to the private backend hostname"
  from_port                    = 80
  to_port                      = 80
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.internal_alb.id
}

resource "aws_security_group" "rds" {
  name        = "${var.name_prefix}-rds"
  description = "Postgres. Only the backend can connect."
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${var.name_prefix}-rds"
  }
}

resource "aws_vpc_security_group_ingress_rule" "rds_from_backend" {
  security_group_id            = aws_security_group.rds.id
  description                  = "Postgres from the backend"
  from_port                    = 5432
  to_port                      = 5432
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.backend.id
}

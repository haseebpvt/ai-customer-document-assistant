resource "aws_lb" "public" {
  name               = "${var.name_prefix}-public"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.public_alb.id]
  subnets            = aws_subnet.public[*].id

  tags = {
    Name = "${var.name_prefix}-public"
  }
}

resource "aws_lb" "internal" {
  name               = "${var.name_prefix}-internal"
  internal           = true
  load_balancer_type = "application"
  security_groups    = [aws_security_group.internal_alb.id]
  subnets            = aws_subnet.private[*].id

  tags = {
    Name = "${var.name_prefix}-internal"
  }
}

resource "aws_lb_target_group" "frontend" {
  name        = "${var.name_prefix}-frontend"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path                = "/"
    matcher             = "200"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 30
    timeout             = 5
  }

  tags = {
    Name = "${var.name_prefix}-frontend"
  }
}

# Public balancer target group for GET and POST /documents.
resource "aws_lb_target_group" "backend_public" {
  name        = "${var.name_prefix}-backend-pub"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path                = "/documents"
    matcher             = "200"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 30
    timeout             = 5
  }

  tags = {
    Name = "${var.name_prefix}-backend-pub"
  }
}

# Internal balancer target group for worker PATCH. Same ECS service, different group.
resource "aws_lb_target_group" "backend_internal" {
  name        = "${var.name_prefix}-backend-int"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path                = "/documents"
    matcher             = "200"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 30
    timeout             = 5
  }

  tags = {
    Name = "${var.name_prefix}-backend-int"
  }
}

resource "aws_lb_listener" "public" {
  load_balancer_arn = aws_lb.public.arn
  port              = 80
  protocol          = "HTTP"

  # Unknown host or path returns 404.
  default_action {
    type = "fixed-response"

    fixed_response {
      content_type = "text/plain"
      message_body = "not found"
      status_code  = "404"
    }
  }
}

resource "aws_lb_listener_rule" "app" {
  listener_arn = aws_lb_listener.public.arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend.arn
  }

  condition {
    host_header {
      values = [local.app_hostname]
    }
  }
}

# PATCH stays off the public balancer. Worker traffic uses the private hostname.
resource "aws_lb_listener_rule" "api_patch_denied" {
  listener_arn = aws_lb_listener.public.arn
  priority     = 20

  action {
    type = "fixed-response"

    fixed_response {
      content_type = "text/plain"
      message_body = "forbidden"
      status_code  = "403"
    }
  }

  condition {
    host_header {
      values = [local.api_hostname]
    }
  }

  condition {
    http_request_method {
      values = ["PATCH"]
    }
  }
}

resource "aws_lb_listener_rule" "api_documents" {
  listener_arn = aws_lb_listener.public.arn
  priority     = 30

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend_public.arn
  }

  condition {
    host_header {
      values = [local.api_hostname]
    }
  }

  condition {
    path_pattern {
      values = ["/documents", "/documents/*"]
    }
  }

  condition {
    # OPTIONS is the browser CORS preflight before POST.
    http_request_method {
      values = ["GET", "POST", "OPTIONS"]
    }
  }
}

resource "aws_lb_listener" "internal" {
  load_balancer_arn = aws_lb.internal.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend_internal.arn
  }
}

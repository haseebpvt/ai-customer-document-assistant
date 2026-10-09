# Public zone for app.<domain> and api.<domain>.
# The zone does not resolve on the internet until its name servers are delegated.
resource "aws_route53_zone" "public" {
  name = var.public_domain

  tags = {
    Name = "${var.name_prefix}-public-zone"
  }
}

resource "aws_route53_record" "app" {
  zone_id = aws_route53_zone.public.zone_id
  name    = local.app_hostname
  type    = "A"

  alias {
    name                   = aws_lb.public.dns_name
    zone_id                = aws_lb.public.zone_id
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "api" {
  zone_id = aws_route53_zone.public.zone_id
  name    = local.api_hostname
  type    = "A"

  alias {
    name                   = aws_lb.public.dns_name
    zone_id                = aws_lb.public.zone_id
    evaluate_target_health = true
  }
}

# Private zone so the worker calls a name, not a task IP.
resource "aws_route53_zone" "private" {
  name = "backend.internal"

  vpc {
    vpc_id = aws_vpc.main.id
  }

  tags = {
    Name = "${var.name_prefix}-private-zone"
  }
}

resource "aws_route53_record" "backend_internal" {
  zone_id = aws_route53_zone.private.zone_id
  name    = local.private_hostname
  type    = "A"

  alias {
    name                   = aws_lb.internal.dns_name
    zone_id                = aws_lb.internal.zone_id
    evaluate_target_health = true
  }
}

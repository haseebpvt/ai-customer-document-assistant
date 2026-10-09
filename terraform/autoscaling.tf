# Frontend stays at one task. It only serves static files.

resource "aws_appautoscaling_target" "backend" {
  max_capacity       = 3
  min_capacity       = 1
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.backend.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "backend_cpu" {
  name               = "${var.name_prefix}-backend-cpu"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.backend.resource_id
  scalable_dimension = aws_appautoscaling_target.backend.scalable_dimension
  service_namespace  = aws_appautoscaling_target.backend.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value = 70

    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }

    scale_out_cooldown = 60
    scale_in_cooldown  = 300
  }
}

resource "aws_appautoscaling_target" "ai" {
  max_capacity       = 5
  min_capacity       = 1
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.ai.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# One visible queue message per running task. At zero tasks the divisor is 1, so a waiting message still scales out.
resource "aws_appautoscaling_policy" "ai_queue" {
  name               = "${var.name_prefix}-ai-queue"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ai.resource_id
  scalable_dimension = aws_appautoscaling_target.ai.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ai.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value = 1

    customized_metric_specification {
      metrics {
        id          = "m1"
        label       = "Visible messages"
        return_data = false

        metric_stat {
          stat = "Average"

          metric {
            namespace   = "AWS/SQS"
            metric_name = "ApproximateNumberOfMessagesVisible"

            dimensions {
              name  = "QueueName"
              value = aws_sqs_queue.documents.name
            }
          }
        }
      }

      metrics {
        id          = "m2"
        label       = "Running tasks"
        return_data = false

        metric_stat {
          stat = "Average"

          metric {
            namespace   = "ECS/ContainerInsights"
            metric_name = "RunningTaskCount"

            dimensions {
              name  = "ClusterName"
              value = aws_ecs_cluster.main.name
            }

            dimensions {
              name  = "ServiceName"
              value = aws_ecs_service.ai.name
            }
          }
        }
      }

      metrics {
        id          = "e1"
        label       = "Messages per task"
        expression  = "m1 / FILL(m2, 1)"
        return_data = true
      }
    }

    scale_out_cooldown = 60
    scale_in_cooldown  = 300
  }
}

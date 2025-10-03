# ECR repositories para armazenar imagens Docker
resource "aws_ecr_repository" "api" {
  name         = "${var.prefix}-api"
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Environment = "production"
    Project     = var.prefix
  }
}

resource "aws_ecr_repository" "job" {
  name         = "${var.prefix}-job"
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Environment = "production"
    Project     = var.prefix
  }
}

# Outputs dos repositórios ECR
output "ecr_api_repository_url" {
  description = "URL do repositório ECR para API"
  value       = aws_ecr_repository.api.repository_url
}

output "ecr_job_repository_url" {
  description = "URL do repositório ECR para Jobs"
  value       = aws_ecr_repository.job.repository_url
}
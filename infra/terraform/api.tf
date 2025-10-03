data "aws_caller_identity" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  ecr_api    = "${local.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${var.prefix}-api:latest"
  ecr_job    = "${local.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${var.prefix}-job:latest"
}

resource "aws_lambda_function" "api" {
  function_name = "${var.prefix}-api"
  role          = aws_iam_role.lambda_exec.arn
  package_type  = "Image"
  image_uri     = local.ecr_api
  timeout       = 20
  memory_size   = 512
  environment {
    variables = {
      MODELS_BUCKET   = aws_s3_bucket.models.bucket
      S3_RAW_BUCKET   = aws_s3_bucket.raw.bucket
      S3_MODELS_BUCKET = aws_s3_bucket.models.bucket
      SYMBOLS         = "AAPL,MSFT,AMZN,GOOGL,META,NVDA,TSLA"
    }
  }
}

resource "aws_apigatewayv2_api" "http_api" {
  name          = "${var.prefix}-http"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "api" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.api.arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.api.id}"
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

# Adicionar stage para API Gateway
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = "$default"
  auto_deploy = true
}

output "api_gateway_url" {
  description = "URL da API Gateway"
  value       = aws_apigatewayv2_api.http_api.api_endpoint
}

output "http_api_url" {
  value = aws_apigatewayv2_api.http_api.api_endpoint
}

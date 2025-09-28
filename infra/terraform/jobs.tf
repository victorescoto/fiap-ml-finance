resource "aws_lambda_function" "job" {
  function_name = "${var.prefix}-job"
  role          = aws_iam_role.lambda_exec.arn
  package_type  = "Image"
  image_uri     = local.ecr_job
  timeout       = 120
  memory_size   = 1024
  environment {
    variables = {
      MODELS_BUCKET = "fiap-fase3-finance-models"
      SYMBOLS       = "AAPL,MSFT,AMZN,GOOGL,META,NVDA,TSLA"
    }
  }
}

# Schedules
resource "aws_cloudwatch_event_rule" "ingest_5m" {
  name                = "${var.prefix}-ingest-5m"
  schedule_expression = "rate(5 minutes)"
}

resource "aws_cloudwatch_event_target" "ingest_5m" {
  rule      = aws_cloudwatch_event_rule.ingest_5m.name
  target_id = "lambda-job-ingest-5m"
  arn       = aws_lambda_function.job.arn
  input     = jsonencode({ JOB_NAME = "ingest_5m" })
}

resource "aws_lambda_permission" "allow_events_ingest5m" {
  statement_id  = "AllowEventInvokeIngest5m"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.job.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.ingest_5m.arn
}

resource "aws_cloudwatch_event_rule" "ingest_1d" {
  name                = "${var.prefix}-ingest-1d"
  schedule_expression = "cron(5 0 * * ? *)" # 00:05 UTC diariamente
}

resource "aws_cloudwatch_event_target" "ingest_1d" {
  rule      = aws_cloudwatch_event_rule.ingest_1d.name
  target_id = "lambda-job-ingest-1d"
  arn       = aws_lambda_function.job.arn
  input     = jsonencode({ JOB_NAME = "ingest_1d" })
}

resource "aws_lambda_permission" "allow_events_ingest1d" {
  statement_id  = "AllowEventInvokeIngest1d"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.job.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.ingest_1d.arn
}

resource "aws_cloudwatch_event_rule" "train_daily" {
  name                = "${var.prefix}-train-daily"
  schedule_expression = "cron(30 0 * * ? *)" # 00:30 UTC diariamente
}

resource "aws_cloudwatch_event_target" "train_daily" {
  rule      = aws_cloudwatch_event_rule.train_daily.name
  target_id = "lambda-job-train-daily"
  arn       = aws_lambda_function.job.arn
  input     = jsonencode({ JOB_NAME = "train_daily" })
}

resource "aws_lambda_permission" "allow_events_train" {
  statement_id  = "AllowEventInvokeTrain"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.job.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.train_daily.arn
}

resource "aws_lambda_function" "job" {
  function_name = "${var.prefix}-job"
  role          = aws_iam_role.lambda_exec.arn
  package_type  = "Image"
  image_uri     = local.ecr_job
  timeout       = 600
  memory_size   = 1024
  environment {
    variables = {
      S3_RAW_BUCKET    = aws_s3_bucket.raw.bucket
      S3_MODELS_BUCKET = aws_s3_bucket.models.bucket
      SYMBOLS          = "AAPL,MSFT,AMZN,GOOGL,META,NVDA,TSLA"
      ML_TRAIN_PERIOD  = "12"
      DATA_DIR         = "/tmp/data"
      MODELS_DIR       = "/tmp/models"
      # Note: Para inicialização histórica (2 anos), use:
      # make run-historical-local ou invoke manualmente com JOB_NAME=ingest_historical
    }
  }
}

# Schedules
resource "aws_cloudwatch_event_rule" "ingest_1h" {
  name                = "${var.prefix}-ingest-1h"
  schedule_expression = "rate(1 hour)"
}

resource "aws_cloudwatch_event_target" "ingest_1h" {
  rule      = aws_cloudwatch_event_rule.ingest_1h.name
  target_id = "lambda-job-ingest-1h"
  arn       = aws_lambda_function.job.arn
  input     = jsonencode({ JOB_NAME = "ingest_1h" })
}

resource "aws_lambda_permission" "allow_events_ingest1h" {
  statement_id  = "AllowEventInvokeIngest1h"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.job.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.ingest_1h.arn
}

resource "aws_cloudwatch_event_rule" "ingest_1d" {
  name                = "${var.prefix}-ingest-1d"
  schedule_expression = "cron(5 0 * * ? *)" # 00:05 UTC diariamente
  description         = "Daily incremental ingestion (2 days only)"
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

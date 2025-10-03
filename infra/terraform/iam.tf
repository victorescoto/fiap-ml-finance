# IAM Role for Lambda
resource "aws_iam_role" "lambda_exec" {
  name = "${var.prefix}-lambda-exec"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Principal = { Service = "lambda.amazonaws.com" },
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# S3 read/write for raw/models
resource "aws_iam_policy" "lambda_s3_rw" {
  name = "${var.prefix}-lambda-s3-rw"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Action = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
      Resource = [
        "arn:aws:s3:::fiap-fase3-finance-raw",
        "arn:aws:s3:::fiap-fase3-finance-raw/*",
        "arn:aws:s3:::fiap-fase3-finance-models",
        "arn:aws:s3:::fiap-fase3-finance-models/*"
      ]
    }]
  })
}

resource "aws_iam_role_policy_attachment" "attach_s3_rw" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_s3_rw.arn
}

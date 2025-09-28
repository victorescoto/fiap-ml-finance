# Lifecycle rules for raw data
resource "aws_s3_bucket_lifecycle_configuration" "raw_lifecycle" {
  bucket = aws_s3_bucket.raw.id

  rule {
    id     = "expire-5m-after-14d"
    status = "Enabled"
    filter { prefix = "interval=5m/" }
    expiration { days = 14 }
  }

  rule {
    id     = "expire-1d-after-365d"
    status = "Enabled"
    filter { prefix = "prices_1d/" }
    expiration { days = 365 }
  }
}

locals {
  raw_bucket     = "${var.prefix}-finance-raw"
  models_bucket  = "${var.prefix}-finance-models"
  site_bucket    = "${var.prefix}-finance-site"
  athena_bucket  = "${var.prefix}-athena-output"
  glue_db_name   = "fiap_fase3_finance"
}

resource "aws_s3_bucket" "raw" {
  bucket = local.raw_bucket
}

resource "aws_s3_bucket_versioning" "raw" {
  bucket = aws_s3_bucket.raw.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket" "models" {
  bucket = local.models_bucket
}

resource "aws_s3_bucket_versioning" "models" {
  bucket = aws_s3_bucket.models.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket" "site" {
  bucket = local.site_bucket
  website {
    index_document = "index.html"
    error_document = "index.html"
  }
}

resource "aws_s3_bucket" "athena" {
  bucket = local.athena_bucket
}

resource "aws_glue_catalog_database" "db" {
  name = local.glue_db_name
}

resource "aws_athena_workgroup" "wg" {
  name = "${var.prefix}-wg"
  configuration {
    enforce_workgroup_configuration = true
    result_configuration {
      output_location = "s3://${local.athena_bucket}/"
    }
  }
  state = "ENABLED"
}

output "buckets" {
  value = {
    raw     = aws_s3_bucket.raw.bucket
    models  = aws_s3_bucket.models.bucket
    site    = aws_s3_bucket.site.bucket
    athena  = aws_s3_bucket.athena.bucket
  }
}

output "glue_database" {
  value = aws_glue_catalog_database.db.name
}

output "athena_workgroup" {
  value = aws_athena_workgroup.wg.name
}

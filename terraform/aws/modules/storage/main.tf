resource "aws_s3_bucket" "webui" {
  bucket        = "${var.environment}-${var.project_name}-webui"
  force_destroy = true

  tags = var.tags
}

resource "aws_s3_bucket_public_access_block" "webui" {
  bucket = aws_s3_bucket.webui.id

  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

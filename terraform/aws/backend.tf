terraform {
  backend "s3" {
    # Configuration provided via -backend-config flags or backend config file:
    # bucket         = "..."
    # region         = "..."
    # dynamodb_table = "..."
    # key            = "..."
  }
}

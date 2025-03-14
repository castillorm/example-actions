provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "test_bucket" {
  bucket = "my-test-bucket-terraform-example"

  tags = {
    Name        = "MyTestBucket"
    Environment = "Dev"
  }
}

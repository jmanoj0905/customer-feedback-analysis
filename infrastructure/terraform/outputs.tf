output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = "${aws_api_gateway_deployment.api_deployment.invoke_url}"
}

output "website_url" {
  description = "S3 website URL"
  value       = "http://${aws_s3_bucket.website_bucket.bucket}.s3-website-${var.aws_region}.amazonaws.com"
}

output "dynamodb_table_name" {
  description = "DynamoDB table name"
  value       = aws_dynamodb_table.feedback_table.name
}

output "analyze_function_name" {
  description = "Analyze feedback Lambda function name"
  value       = aws_lambda_function.analyze_feedback.function_name
}

output "analytics_function_name" {
  description = "Get analytics Lambda function name"
  value       = aws_lambda_function.get_analytics.function_name
}

output "s3_bucket_name" {
  description = "S3 bucket name for website"
  value       = aws_s3_bucket.website_bucket.bucket
}

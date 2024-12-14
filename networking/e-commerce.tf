# Main provider configuration
provider "aws" {
  region = "eu-west-1"  # Primary region (Frankfurt)
}

# Variables
variable "environment" {
  default = "prod"
}

variable "regions" {
  type = list(string)
  default = ["eu-west-1", "us-east-1", "ap-southeast-1"]  # Multi-region deployment
}

# CDN Configuration
resource "aws_cloudfront_distribution" "cdn" {
  enabled = true
  
  origin {
    domain_name = aws_s3_bucket.static_assets.bucket_regional_domain_name
    origin_id   = "S3-static-assets"
  }
  
  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-static-assets"
    
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
    
    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }
  
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
  
  viewer_certificate {
    acm_certificate_arn = aws_acm_certificate.cdn_cert.arn
    ssl_support_method  = "sni-only"
  }
}

# Regional Application Load Balancer
resource "aws_lb" "app_gateway" {
  name               = "${var.environment}-app-gateway"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id
  
  enable_deletion_protection = true
  
  tags = {
    Environment = var.environment
  }
}

# WAF Configuration
resource "aws_wafv2_web_acl" "main" {
  name        = "${var.environment}-web-acl"
  description = "WAF rules for e-commerce platform"
  scope       = "REGIONAL"
  
  default_action {
    allow {}
  }
  
  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 1
    
    override_action {
      none {}
    }
    
    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }
    
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name               = "AWSManagedRulesCommonRuleSetMetric"
      sampled_requests_enabled  = true
    }
  }
}

# EKS Cluster for Microservices
resource "aws_eks_cluster" "main" {
  name     = "${var.environment}-eks-cluster"
  role_arn = aws_iam_role.eks_cluster.arn
  
  vpc_config {
    subnet_ids = aws_subnet.private[*].id
  }
  
  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy
  ]
}

# Node Group for EKS
resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "main"
  node_role_arn   = aws_iam_role.eks_nodes.arn
  subnet_ids      = aws_subnet.private[*].id
  
  scaling_config {
    desired_size = 3
    max_size     = 5
    min_size     = 1
  }
  
  instance_types = ["t3.large"]
}

# RDS Multi-AZ Database
resource "aws_db_instance" "main" {
  identifier           = "${var.environment}-db"
  allocated_storage    = 100
  storage_type         = "gp3"
  engine              = "postgresql"
  engine_version       = "13.7"
  instance_class      = "db.r5.2xlarge"
  multi_az            = true
  name                = "ecommerce"
  username            = "admin"
  password            = random_password.db_password.result
  skip_final_snapshot = false
  
  vpc_security_group_ids = [aws_security_group.db.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
}

# ElastiCache Redis Cluster
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "${var.environment}-redis"
  engine              = "redis"
  node_type           = "cache.r5.large"
  num_cache_nodes     = 3
  parameter_group_name = "default.redis6.x"
  port                = 6379
  
  subnet_group_name    = aws_elasticache_subnet_group.main.name
  security_group_ids   = [aws_security_group.redis.id]
}

# Amazon MSK (Kafka) Cluster
resource "aws_msk_cluster" "events" {
  cluster_name           = "${var.environment}-kafka"
  kafka_version          = "2.8.1"
  number_of_broker_nodes = 3
  
  broker_node_group_info {
    instance_type   = "kafka.m5.large"
    client_subnets  = aws_subnet.private[*].id
    security_groups = [aws_security_group.kafka.id]
    
    storage_info {
      ebs_storage_info {
        volume_size = 100
      }
    }
  }
}

# Elasticsearch Domain
resource "aws_elasticsearch_domain" "search" {
  domain_name           = "${var.environment}-search"
  elasticsearch_version = "7.10"
  
  cluster_config {
    instance_type  = "r5.large.elasticsearch"
    instance_count = 3
  }
  
  ebs_options {
    ebs_enabled = true
    volume_size = 100
  }
  
  vpc_options {
    subnet_ids         = [aws_subnet.private[0].id]
    security_group_ids = [aws_security_group.elasticsearch.id]
  }
}

# CloudWatch Monitoring
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.environment}-dashboard"
  
  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        width  = 12
        height = 6
        
        properties = {
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", aws_lb.app_gateway.arn]
          ]
          period = 300
          stat   = "Sum"
          region = "eu-west-1"
          title  = "ALB Request Count"
        }
      }
    ]
  })
}

# Outputs
output "eks_cluster_endpoint" {
  value = aws_eks_cluster.main.endpoint
}

output "cdn_domain_name" {
  value = aws_cloudfront_distribution.cdn.domain_name
}

output "db_endpoint" {
  value = aws_db_instance.main.endpoint
}

output "redis_endpoint" {
  value = aws_elasticache_cluster.redis.cache_nodes[0].address
}

output "kafka_brokers" {
  value = aws_msk_cluster.events.bootstrap_brokers
}

output "elasticsearch_endpoint" {
  value = aws_elasticsearch_domain.search.endpoint
}

variable "key_name" {
  description = "EC2 Key Pair Name"
  type        = string
  default     = "dev-internal"  
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}

variable "region" {
  description = "AWS Region"
  type        = string
  default     = "ap-south-1"
}

variable "ami_id" {
  description = "Ubuntu 22.04 AMI ID"
  type        = string
  default     = "ami-03bb6d83c60fc5f7c"
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
  default     = "vpc-07470559ed4c11690"
}

variable "subnet_id" {
  description = "Subnet ID"
  type        = string
  default     = "subnet-0540cf3953564acb7"
}
variable "s3_bucket_name" {
  description = "S3 bucket name"
  type        = string
  default     = "task-tracker-logs-api"
}

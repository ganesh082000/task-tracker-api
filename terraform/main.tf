# Security Group
resource "aws_security_group" "task_sg" {
  name        = "task-sg"
  description = "Allow HTTP and FastAPI ports"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# EC2 Instance
resource "aws_instance" "task_ec2" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  key_name               = var.key_name
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [aws_security_group.task_sg.id]
  associate_public_ip_address = true

  tags = {
    Name = "task-tracker-ec2"
  }
}

# S3 Bucket
resource "aws_s3_bucket" "task_bucket" {
  bucket = var.s3_bucket_name

  tags = {
    Name = "task-tracker-s3"
  }
}

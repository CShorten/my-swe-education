# Configure the AWS Provider
provider "aws" {
  region = "us-west-2"
}

# Define variables
variable "environment" {
  description = "Environment (dev/staging/prod)"
  type        = string
  default     = "dev"
}

variable "instance_type" {
  description = "GPU instance type"
  type        = string
  default     = "p3.2xlarge"  # Comes with 1 NVIDIA Tesla V100 GPU
}

variable "ami_id" {
  description = "Deep Learning AMI ID"
  type        = string
  default     = "ami-0e4841c3bb7d47d27"  # AWS Deep Learning AMI GPU PyTorch 2.0.1
}

# Create a VPC for ML workloads
resource "aws_vpc" "ml_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "${var.environment}-ml-vpc"
    Environment = var.environment
    Purpose     = "Machine Learning"
  }
}

# Create public subnet
resource "aws_subnet" "ml_public" {
  vpc_id                  = aws_vpc.ml_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-west-2a"
  map_public_ip_on_launch = true

  tags = {
    Name        = "${var.environment}-ml-public-subnet"
    Environment = var.environment
  }
}

# Create Internet Gateway
resource "aws_internet_gateway" "ml_igw" {
  vpc_id = aws_vpc.ml_vpc.id

  tags = {
    Name        = "${var.environment}-ml-igw"
    Environment = var.environment
  }
}

# Create Route Table
resource "aws_route_table" "ml_public" {
  vpc_id = aws_vpc.ml_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.ml_igw.id
  }

  tags = {
    Name        = "${var.environment}-ml-rt"
    Environment = var.environment
  }
}

# Associate public subnet with route table
resource "aws_route_table_association" "ml_public" {
  subnet_id      = aws_subnet.ml_public.id
  route_table_id = aws_route_table.ml_public.id
}

# Create Security Group for ML instances
resource "aws_security_group" "ml_security" {
  name        = "${var.environment}-ml-sg"
  description = "Security group for ML instances with GPU"
  vpc_id      = aws_vpc.ml_vpc.id

  ingress {
    description = "SSH from anywhere"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Jupyter Notebook"
    from_port   = 8888
    to_port     = 8888
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "TensorBoard"
    from_port   = 6006
    to_port     = 6006
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.environment}-ml-sg"
    Environment = var.environment
  }
}

# Create EBS volume for ML data
resource "aws_ebs_volume" "ml_data" {
  availability_zone = "us-west-2a"
  size             = 100
  type             = "gp3"
  iops             = 3000

  tags = {
    Name        = "${var.environment}-ml-data"
    Environment = var.environment
  }
}

# Create GPU Instance
resource "aws_instance" "gpu_instance" {
  ami           = var.ami_id
  instance_type = var.instance_type

  subnet_id                   = aws_subnet.ml_public.id
  vpc_security_group_ids      = [aws_security_group.ml_security.id]
  associate_public_ip_address = true

  root_block_device {
    volume_size = 100
    volume_type = "gp3"
  }

  user_data = <<-EOF
              #!/bin/bash
              # Update system
              sudo apt-get update && sudo apt-get upgrade -y

              # Install monitoring tools
              sudo apt-get install -y htop nvidia-smi

              # Set up auto mounting of ML data volume
              sudo mkfs -t ext4 /dev/xvdf
              sudo mkdir /ml_data
              sudo mount /dev/xvdf /ml_data
              echo '/dev/xvdf /ml_data ext4 defaults 0 0' | sudo tee -a /etc/fstab

              # Start Jupyter notebook server
              jupyter notebook --generate-config
              echo "c.NotebookApp.ip = '0.0.0.0'" >> ~/.jupyter/jupyter_notebook_config.py
              echo "c.NotebookApp.open_browser = False" >> ~/.jupyter/jupyter_notebook_config.py
              echo "c.NotebookApp.port = 8888" >> ~/.jupyter/jupyter_notebook_config.py
              EOF

  tags = {
    Name        = "${var.environment}-gpu-instance"
    Environment = var.environment
    Purpose     = "Machine Learning"
  }
}

# Attach EBS volume to instance
resource "aws_volume_attachment" "ml_data_attach" {
  device_name = "/dev/xvdf"
  volume_id   = aws_ebs_volume.ml_data.id
  instance_id = aws_instance.gpu_instance.id
}

# Define outputs
output "instance_public_ip" {
  description = "Public IP address of the GPU instance"
  value       = aws_instance.gpu_instance.public_ip
}

output "instance_id" {
  description = "ID of the GPU instance"
  value       = aws_instance.gpu_instance.id
}

output "jupyter_url" {
  description = "URL for Jupyter Notebook (remember to set up password)"
  value       = "http://${aws_instance.gpu_instance.public_ip}:8888"
}

output "tensorboard_url" {
  description = "URL for TensorBoard"
  value       = "http://${aws_instance.gpu_instance.public_ip}:6006"
}

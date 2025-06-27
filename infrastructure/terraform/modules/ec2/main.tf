variable "instance_count" {
  description = "Number of instances to create"
  type        = number
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
}

variable "subnet_id" {
  description = "Subnet ID for instances"
  type        = string
}

variable "security_group_id" {
  description = "Security group ID"
  type        = string
}

variable "iam_instance_profile" {
  description = "IAM instance profile name"
  type        = string
}

variable "tags" {
  description = "Tags to apply to instances"
  type        = map(string)
}

# Get latest Amazon Linux 2 AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# EC2 Instances
resource "aws_instance" "test" {
  count = var.instance_count

  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [var.security_group_id]
  iam_instance_profile   = var.iam_instance_profile

  # Enable detailed monitoring
  monitoring = true

  # User data script for CloudWatch agent
  user_data = <<-EOF
    #!/bin/bash
    yum update -y
    
    # Install CloudWatch agent
    wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
    rpm -U ./amazon-cloudwatch-agent.rpm
    
    # Install stress tool for testing
    amazon-linux-extras install epel -y
    yum install stress -y
    
    # Tag instance with its ID
    INSTANCE_ID=$(ec2-metadata --instance-id | cut -d " " -f 2)
    aws ec2 create-tags --resources $INSTANCE_ID --tags Key=InstanceId,Value=$INSTANCE_ID --region ${data.aws_region.current.name}
  EOF

  tags = merge(
    var.tags,
    {
      Name = format("%s-%d", lookup(var.tags, "Name", "instance"), count.index + 1)
    }
  )
}

# Data source for current region
data "aws_region" "current" {}

# Output instance IDs
output "instance_ids" {
  value = aws_instance.test[*].id
}

output "instance_private_ips" {
  value = aws_instance.test[*].private_ip
}
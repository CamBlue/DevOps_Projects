# Terraform Three-Tier VPC Architecture

## Project Overview
**Difficulty:** Intermediate  
**Estimated Time:** 4-6 hours  
**Skills Practiced:** VPC Design, Multi-tier Architecture, Terraform Modules, NAT Gateways, Bastion Hosts

### What You'll Build
A production-ready three-tier network architecture:
- **Public Tier:** Internet-facing resources (load balancer, bastion)
- **Application Tier:** Private web/app servers with NAT internet access
- **Database Tier:** Isolated database servers with no internet access
- Multiple availability zones for high availability
- NAT Gateways for private subnet internet access
- Bastion host for secure SSH access
- Network ACLs and security groups for defense in depth

### Why This Matters
This is how real production environments are structured. You'll learn:
- Network isolation and security best practices
- High availability design patterns
- Cost-effective NAT strategies
- Bastion host security

### Prerequisites
- Completed "Terraform Single VM" project
- Understanding of VPC, subnets, route tables
- AWS CLI configured
- Terraform 1.7+ installed

---

## Architecture Diagram

```
Internet
    │
[Internet Gateway]
    │
┌───┴────────────────────────────────────────┐
│         PUBLIC SUBNETS (10.0.1.0/24)       │
│   - Load Balancer                          │
│   - Bastion Host                           │
│   - NAT Gateways                           │
└───┬────────────────────────────────────────┘
    │
┌───┴────────────────────────────────────────┐
│       APPLICATION SUBNETS (10.0.2.0/24)    │
│   - Web Servers                            │
│   - Application Servers                    │
│   - Internet via NAT Gateway               │
└───┬────────────────────────────────────────┘
    │
┌───┴────────────────────────────────────────┐
│        DATABASE SUBNETS (10.0.3.0/24)      │
│   - RDS Instances                          │
│   - No Internet Access                     │
│   - Only accepts traffic from App tier     │
└────────────────────────────────────────────┘
```

---

## Step-by-Step Implementation

### Step 1: Project Structure Setup

```bash
mkdir terraform-three-tier-vpc
cd terraform-three-tier-vpc

# Create file structure
touch main.tf
touch variables.tf
touch outputs.tf
touch terraform.tfvars
touch .gitignore

# Create module directories
mkdir -p modules/{vpc,security-groups,bastion,compute}

# VPC module files
touch modules/vpc/{main.tf,variables.tf,outputs.tf}

# Security Groups module files
touch modules/security-groups/{main.tf,variables.tf,outputs.tf}

# Bastion module files
touch modules/bastion/{main.tf,variables.tf,outputs.tf}

# Compute module files
touch modules/compute/{main.tf,variables.tf,outputs.tf}
```

**Final structure:**
```
terraform-three-tier-vpc/
├── main.tf
├── variables.tf
├── outputs.tf
├── terraform.tfvars
├── .gitignore
└── modules/
    ├── vpc/
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── security-groups/
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── bastion/
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    └── compute/
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

### Step 2: VPC Module Implementation

**File: `modules/vpc/variables.tf`**
```hcl
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
}

variable "app_subnet_cidrs" {
  description = "CIDR blocks for application subnets"
  type        = list(string)
}

variable "db_subnet_cidrs" {
  description = "CIDR blocks for database subnets"
  type        = list(string)
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnets"
  type        = bool
  default     = true
}

variable "single_nat_gateway" {
  description = "Use single NAT Gateway (cost savings)"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
```

**File: `modules/vpc/main.tf`**
```hcl
# Create VPC
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-vpc"
    }
  )
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-igw"
    }
  )
}

# Public Subnets
resource "aws_subnet" "public" {
  count                   = length(var.public_subnet_cidrs)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-public-subnet-${count.index + 1}"
      Tier = "Public"
    }
  )
}

# Application (Private) Subnets
resource "aws_subnet" "app" {
  count             = length(var.app_subnet_cidrs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.app_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-app-subnet-${count.index + 1}"
      Tier = "Application"
    }
  )
}

# Database (Private) Subnets
resource "aws_subnet" "db" {
  count             = length(var.db_subnet_cidrs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.db_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-db-subnet-${count.index + 1}"
      Tier = "Database"
    }
  )
}

# Elastic IPs for NAT Gateways
resource "aws_eip" "nat" {
  count  = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : length(var.availability_zones)) : 0
  domain = "vpc"

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-nat-eip-${count.index + 1}"
    }
  )

  depends_on = [aws_internet_gateway.main]
}

# NAT Gateways
resource "aws_nat_gateway" "main" {
  count         = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : length(var.availability_zones)) : 0
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-nat-gw-${count.index + 1}"
    }
  )

  depends_on = [aws_internet_gateway.main]
}

# Public Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-public-rt"
    }
  )
}

# Associate Public Subnets with Public Route Table
resource "aws_route_table_association" "public" {
  count          = length(var.public_subnet_cidrs)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Application Route Tables
resource "aws_route_table" "app" {
  count  = length(var.app_subnet_cidrs)
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = var.single_nat_gateway ? aws_nat_gateway.main[0].id : aws_nat_gateway.main[count.index].id
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-app-rt-${count.index + 1}"
    }
  )
}

# Associate App Subnets with App Route Tables
resource "aws_route_table_association" "app" {
  count          = length(var.app_subnet_cidrs)
  subnet_id      = aws_subnet.app[count.index].id
  route_table_id = aws_route_table.app[count.index].id
}

# Database Route Tables (no internet access)
resource "aws_route_table" "db" {
  count  = length(var.db_subnet_cidrs)
  vpc_id = aws_vpc.main.id

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-db-rt-${count.index + 1}"
    }
  )
}

# Associate DB Subnets with DB Route Tables
resource "aws_route_table_association" "db" {
  count          = length(var.db_subnet_cidrs)
  subnet_id      = aws_subnet.db[count.index].id
  route_table_id = aws_route_table.db[count.index].id
}

# VPC Flow Logs (optional but recommended)
resource "aws_flow_log" "main" {
  iam_role_arn    = aws_iam_role.vpc_flow_logs.arn
  log_destination = aws_cloudwatch_log_group.vpc_flow_logs.arn
  traffic_type    = "ALL"
  vpc_id          = aws_vpc.main.id

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-vpc-flow-logs"
    }
  )
}

# CloudWatch Log Group for VPC Flow Logs
resource "aws_cloudwatch_log_group" "vpc_flow_logs" {
  name              = "/aws/vpc/${var.environment}-flow-logs"
  retention_in_days = 7

  tags = var.tags
}

# IAM Role for VPC Flow Logs
resource "aws_iam_role" "vpc_flow_logs" {
  name = "${var.environment}-vpc-flow-logs-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "vpc-flow-logs.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# IAM Policy for VPC Flow Logs
resource "aws_iam_role_policy" "vpc_flow_logs" {
  name = "${var.environment}-vpc-flow-logs-policy"
  role = aws_iam_role.vpc_flow_logs.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Effect = "Allow"
        Resource = "*"
      }
    ]
  })
}
```

**File: `modules/vpc/outputs.tf`**
```hcl
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "vpc_cidr" {
  description = "VPC CIDR block"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "app_subnet_ids" {
  description = "List of application subnet IDs"
  value       = aws_subnet.app[*].id
}

output "db_subnet_ids" {
  description = "List of database subnet IDs"
  value       = aws_subnet.db[*].id
}

output "nat_gateway_ids" {
  description = "List of NAT Gateway IDs"
  value       = aws_nat_gateway.main[*].id
}

output "internet_gateway_id" {
  description = "Internet Gateway ID"
  value       = aws_internet_gateway.main.id
}
```

### Step 3: Security Groups Module

**File: `modules/security-groups/variables.tf`**
```hcl
variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "allowed_ssh_cidr" {
  description = "CIDR allowed to SSH to bastion"
  type        = string
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
```

**File: `modules/security-groups/main.tf`**
```hcl
# Bastion Security Group
resource "aws_security_group" "bastion" {
  name        = "${var.environment}-bastion-sg"
  description = "Security group for bastion host"
  vpc_id      = var.vpc_id

  # SSH from specific CIDR
  ingress {
    description = "SSH from allowed CIDR"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
  }

  # All outbound
  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-bastion-sg"
    }
  )
}

# Application Load Balancer Security Group
resource "aws_security_group" "alb" {
  name        = "${var.environment}-alb-sg"
  description = "Security group for application load balancer"
  vpc_id      = var.vpc_id

  # HTTP from internet
  ingress {
    description = "HTTP from internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS from internet
  ingress {
    description = "HTTPS from internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # All outbound
  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-alb-sg"
    }
  )
}

# Application Tier Security Group
resource "aws_security_group" "app" {
  name        = "${var.environment}-app-sg"
  description = "Security group for application servers"
  vpc_id      = var.vpc_id

  # HTTP from ALB
  ingress {
    description     = "HTTP from ALB"
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  # SSH from bastion
  ingress {
    description     = "SSH from bastion"
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.bastion.id]
  }

  # All outbound
  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-app-sg"
    }
  )
}

# Database Security Group
resource "aws_security_group" "db" {
  name        = "${var.environment}-db-sg"
  description = "Security group for database servers"
  vpc_id      = var.vpc_id

  # MySQL/PostgreSQL from app tier
  ingress {
    description     = "Database from application tier"
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  # PostgreSQL alternative
  ingress {
    description     = "PostgreSQL from application tier"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  # No outbound internet (only VPC)
  egress {
    description = "Outbound to VPC only"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [data.aws_vpc.selected.cidr_block]
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-db-sg"
    }
  )
}

# Data source for VPC CIDR
data "aws_vpc" "selected" {
  id = var.vpc_id
}
```

**File: `modules/security-groups/outputs.tf`**
```hcl
output "bastion_sg_id" {
  description = "Bastion security group ID"
  value       = aws_security_group.bastion.id
}

output "alb_sg_id" {
  description = "ALB security group ID"
  value       = aws_security_group.alb.id
}

output "app_sg_id" {
  description = "Application security group ID"
  value       = aws_security_group.app.id
}

output "db_sg_id" {
  description = "Database security group ID"
  value       = aws_security_group.db.id
}
```

### Step 4: Bastion Module

**File: `modules/bastion/variables.tf`**
```hcl
variable "environment" {
  description = "Environment name"
  type        = string
}

variable "subnet_id" {
  description = "Subnet ID for bastion"
  type        = string
}

variable "security_group_id" {
  description = "Security group ID"
  type        = string
}

variable "key_name" {
  description = "SSH key name"
  type        = string
}

variable "instance_type" {
  description = "Instance type"
  type        = string
  default     = "t2.micro"
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
```

**File: `modules/bastion/main.tf`**
```hcl
# Latest Amazon Linux 2023 AMI
data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Bastion Host
resource "aws_instance" "bastion" {
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = var.instance_type
  key_name               = var.key_name
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [var.security_group_id]

  user_data = <<-EOF
              #!/bin/bash
              yum update -y
              yum install -y htop tmux

              # Configure SSH
              echo "ClientAliveInterval 60" >> /etc/ssh/sshd_config
              echo "ClientAliveCountMax 120" >> /etc/ssh/sshd_config
              systemctl restart sshd
              EOF

  root_block_device {
    volume_size           = 8
    volume_type           = "gp3"
    delete_on_termination = true
    encrypted             = true
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-bastion"
      Role = "Bastion"
    }
  )
}

# Elastic IP for Bastion
resource "aws_eip" "bastion" {
  instance = aws_instance.bastion.id
  domain   = "vpc"

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-bastion-eip"
    }
  )
}
```

**File: `modules/bastion/outputs.tf`**
```hcl
output "bastion_instance_id" {
  description = "Bastion instance ID"
  value       = aws_instance.bastion.id
}

output "bastion_public_ip" {
  description = "Bastion public IP"
  value       = aws_eip.bastion.public_ip
}

output "bastion_private_ip" {
  description = "Bastion private IP"
  value       = aws_instance.bastion.private_ip
}
```

### Step 5: Root Configuration

**File: `variables.tf`**
```hcl
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "public_subnet_cidrs" {
  description = "Public subnet CIDRs"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "app_subnet_cidrs" {
  description = "Application subnet CIDRs"
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24"]
}

variable "db_subnet_cidrs" {
  description = "Database subnet CIDRs"
  type        = list(string)
  default     = ["10.0.21.0/24", "10.0.22.0/24"]
}

variable "single_nat_gateway" {
  description = "Use single NAT gateway (cost savings)"
  type        = bool
  default     = true  # Set false for production HA
}

variable "ssh_key_name" {
  description = "SSH key pair name"
  type        = string
}

variable "allowed_ssh_cidr" {
  description = "CIDR allowed to SSH"
  type        = string
}

variable "project_tags" {
  description = "Project tags"
  type        = map(string)
  default = {
    Project   = "Three-Tier-VPC"
    ManagedBy = "Terraform"
  }
}
```

**File: `terraform.tfvars`**
```hcl
aws_region         = "us-east-1"
environment        = "dev"
vpc_cidr           = "10.0.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b"]

public_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24"]
app_subnet_cidrs    = ["10.0.11.0/24", "10.0.12.0/24"]
db_subnet_cidrs     = ["10.0.21.0/24", "10.0.22.0/24"]

# Cost optimization: single NAT GW (change to false for prod HA)
single_nat_gateway = true

ssh_key_name = "your-key-name"

# CHANGE THIS TO YOUR IP
allowed_ssh_cidr = "YOUR_IP/32"

project_tags = {
  Project     = "DevOps-Learning"
  Environment = "Development"
  Architecture = "Three-Tier"
  ManagedBy   = "Terraform"
}
```

**File: `main.tf`**
```hcl
terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = var.project_tags
  }
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"

  vpc_cidr            = var.vpc_cidr
  environment         = var.environment
  availability_zones  = var.availability_zones
  public_subnet_cidrs = var.public_subnet_cidrs
  app_subnet_cidrs    = var.app_subnet_cidrs
  db_subnet_cidrs     = var.db_subnet_cidrs
  enable_nat_gateway  = true
  single_nat_gateway  = var.single_nat_gateway
  tags                = var.project_tags
}

# Security Groups Module
module "security_groups" {
  source = "./modules/security-groups"

  vpc_id           = module.vpc.vpc_id
  environment      = var.environment
  allowed_ssh_cidr = var.allowed_ssh_cidr
  tags             = var.project_tags
}

# Bastion Module
module "bastion" {
  source = "./modules/bastion"

  environment       = var.environment
  subnet_id         = module.vpc.public_subnet_ids[0]
  security_group_id = module.security_groups.bastion_sg_id
  key_name          = var.ssh_key_name
  instance_type     = "t2.micro"
  tags              = var.project_tags
}
```

**File: `outputs.tf`**
```hcl
# VPC Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnet_ids
}

output "app_subnet_ids" {
  description = "Application subnet IDs"
  value       = module.vpc.app_subnet_ids
}

output "db_subnet_ids" {
  description = "Database subnet IDs"
  value       = module.vpc.db_subnet_ids
}

# Security Group Outputs
output "bastion_sg_id" {
  description = "Bastion security group ID"
  value       = module.security_groups.bastion_sg_id
}

output "alb_sg_id" {
  description = "ALB security group ID"
  value       = module.security_groups.alb_sg_id
}

output "app_sg_id" {
  description = "Application security group ID"
  value       = module.security_groups.app_sg_id
}

output "db_sg_id" {
  description = "Database security group ID"
  value       = module.security_groups.db_sg_id
}

# Bastion Outputs
output "bastion_public_ip" {
  description = "Bastion public IP"
  value       = module.bastion.bastion_public_ip
}

output "bastion_ssh_command" {
  description = "SSH command for bastion"
  value       = "ssh -i ~/.ssh/${var.ssh_key_name}.pem ec2-user@${module.bastion.bastion_public_ip}"
}

# NAT Gateway Outputs
output "nat_gateway_ids" {
  description = "NAT Gateway IDs"
  value       = module.vpc.nat_gateway_ids
}
```

### Step 6: Deploy Infrastructure

```bash
# Initialize
terraform init

# Format
terraform fmt -recursive

# Validate
terraform validate

# Plan
terraform plan

# Apply
terraform apply
```

### Step 7: Verify Architecture

**SSH to bastion:**
```bash
ssh -i ~/.ssh/your-key.pem ec2-user@$(terraform output -raw bastion_public_ip)
```

**Check connectivity from bastion:**
```bash
# On bastion - test NAT gateway internet access
curl ifconfig.me

# View route tables
aws ec2 describe-route-tables --region us-east-1
```

### Step 8: Clean Up

```bash
terraform destroy
```

---

## Success Criteria
- [ ] VPC created with proper CIDR
- [ ] 6 subnets created (2 per tier, multi-AZ)
- [ ] NAT Gateway provides internet to app tier
- [ ] Database tier has no internet access
- [ ] Bastion accessible via SSH
- [ ] Security groups properly isolate tiers
- [ ] VPC Flow Logs enabled

## Cost Estimation
- NAT Gateway: $0.045/hour = **$32/month** (main cost)
- Elastic IPs: $0.005/hour (if unattached)
- Bastion t2.micro: $8.50/month
- **Total:** ~$40-45/month
- **With single NAT:** ~$40/month
- **With dual NAT (HA):** ~$72/month

## Extension Ideas
1. Add Application Load Balancer in public tier
2. Deploy Auto Scaling Group in app tier
3. Add RDS database in database tier
4. Implement VPC Peering with another VPC
5. Add Transit Gateway for multi-VPC connectivity
6. Implement Systems Manager Session Manager (remove bastion)
7. Add CloudWatch dashboards for network monitoring

---

**Completion Time:** 4-6 hours  
**Difficulty:** Intermediate  
**AWS Cost:** $40-45/month (destroy when done testing)

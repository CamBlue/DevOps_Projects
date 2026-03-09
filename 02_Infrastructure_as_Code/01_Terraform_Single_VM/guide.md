# Terraform Single VM Deployment

## Project Overview
**Difficulty:** Beginner  
**Estimated Time:** 2-3 hours  
**Skills Practiced:** Terraform Basics, AWS EC2, HCL Syntax, Infrastructure as Code

### What You'll Build
A foundational Terraform project that provisions:
- Single EC2 instance in AWS
- VPC with subnet configuration
- Security group with SSH access
- SSH key pair for access
- Elastic IP for stable addressing
- Outputs for connection details

### Why This Matters
This is your first Infrastructure as Code project. You'll learn to declare infrastructure in code, understand Terraform's workflow (init, plan, apply), and master the basics that scale to complex architectures.

### Prerequisites
- AWS account with billing enabled
- AWS CLI installed and configured
- Terraform 1.7+ installed
- SSH key pair generated locally
- Basic understanding of EC2 and VPC concepts

---

## Step-by-Step Implementation

### Step 1: Install and Verify Terraform

**MacOS:**
```bash
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
```

**Linux:**
```bash
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform
```

**Windows:**
```powershell
choco install terraform
```

**Verify installation:**
```bash
terraform version
# Should show: Terraform v1.7.0 or later
```

### Step 2: Configure AWS Credentials

**Option A: AWS CLI (Recommended)**
```bash
aws configure
# Enter:
# - AWS Access Key ID
# - AWS Secret Access Key  
# - Default region: us-east-1
# - Default output format: json

# Verify
aws sts get-caller-identity
```

**Option B: Environment Variables**
```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

### Step 3: Create Project Structure

```bash
mkdir terraform-single-vm
cd terraform-single-vm

# Create Terraform files
touch main.tf
touch variables.tf
touch outputs.tf
touch terraform.tfvars
touch .gitignore
```

**Project structure:**
```
terraform-single-vm/
├── main.tf           # Main infrastructure code
├── variables.tf      # Variable definitions
├── outputs.tf        # Output values
├── terraform.tfvars  # Variable values (DO NOT COMMIT)
└── .gitignore        # Git ignore file
```

### Step 4: Create .gitignore

**File: `.gitignore`**
```
# Local .terraform directories
**/.terraform/*

# .tfstate files
*.tfstate
*.tfstate.*

# Crash log files
crash.log
crash.*.log

# Exclude variable values
*.tfvars
*.tfvars.json

# Ignore override files
override.tf
override.tf.json
*_override.tf
*_override.tf.json

# SSH keys
*.pem
*.pub

# CLI configuration files
.terraformrc
terraform.rc
```

### Step 5: Define Variables

**File: `variables.tf`**
```hcl
# AWS Region
variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

# Instance Configuration
variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}

variable "instance_name" {
  description = "Name tag for the EC2 instance"
  type        = string
  default     = "terraform-demo-vm"
}

# Network Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "subnet_cidr" {
  description = "CIDR block for subnet"
  type        = string
  default     = "10.0.1.0/24"
}

# SSH Configuration
variable "ssh_key_name" {
  description = "Name of SSH key pair"
  type        = string
}

variable "ssh_public_key_path" {
  description = "Path to SSH public key"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

# Security
variable "allowed_ssh_cidr" {
  description = "CIDR block allowed to SSH"
  type        = string
  default     = "0.0.0.0/0"  # CHANGE THIS to your IP for production
}

# Tags
variable "project_tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "Terraform-Demo"
    Environment = "Dev"
    ManagedBy   = "Terraform"
  }
}
```

### Step 6: Set Variable Values

**File: `terraform.tfvars`**
```hcl
aws_region            = "us-east-1"
instance_type         = "t2.micro"
instance_name         = "my-first-terraform-vm"
ssh_key_name          = "my-terraform-key"
ssh_public_key_path   = "~/.ssh/id_rsa.pub"

# IMPORTANT: Change this to your IP for security
# Get your IP: curl ifconfig.me
allowed_ssh_cidr      = "YOUR_IP_ADDRESS/32"

project_tags = {
  Project     = "DevOps-Learning"
  Environment = "Development"
  ManagedBy   = "Terraform"
  Owner       = "YourName"
}
```

### Step 7: Write Main Infrastructure Code

**File: `main.tf`**
```hcl
# Configure Terraform
terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Configure AWS Provider
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = var.project_tags
  }
}

# Data source: Latest Amazon Linux 2023 AMI
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

# Create VPC
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.instance_name}-vpc"
  }
}

# Create Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.instance_name}-igw"
  }
}

# Create Public Subnet
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.subnet_cidr
  map_public_ip_on_launch = true
  availability_zone       = data.aws_availability_zones.available.names[0]

  tags = {
    Name = "${var.instance_name}-public-subnet"
  }
}

# Data source: Available AZs
data "aws_availability_zones" "available" {
  state = "available"
}

# Create Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${var.instance_name}-public-rt"
  }
}

# Associate Route Table with Subnet
resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# Create Security Group
resource "aws_security_group" "instance" {
  name        = "${var.instance_name}-sg"
  description = "Security group for ${var.instance_name}"
  vpc_id      = aws_vpc.main.id

  # SSH access
  ingress {
    description = "SSH from allowed CIDR"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
  }

  # HTTP access (optional)
  ingress {
    description = "HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS access (optional)
  ingress {
    description = "HTTPS from anywhere"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # All outbound traffic
  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.instance_name}-sg"
  }
}

# Create SSH Key Pair
resource "aws_key_pair" "deployer" {
  key_name   = var.ssh_key_name
  public_key = file(pathexpand(var.ssh_public_key_path))

  tags = {
    Name = var.ssh_key_name
  }
}

# Create EC2 Instance
resource "aws_instance" "main" {
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.deployer.key_name
  vpc_security_group_ids = [aws_security_group.instance.id]
  subnet_id              = aws_subnet.public.id

  # User data script (optional - installs Apache)
  user_data = <<-EOF
              #!/bin/bash
              yum update -y
              yum install -y httpd
              systemctl start httpd
              systemctl enable httpd
              echo "<h1>Hello from Terraform!</h1>" > /var/www/html/index.html
              EOF

  # Root volume configuration
  root_block_device {
    volume_size           = 8
    volume_type           = "gp3"
    delete_on_termination = true
    encrypted             = true

    tags = {
      Name = "${var.instance_name}-root-volume"
    }
  }

  tags = {
    Name = var.instance_name
  }

  # Ensure key pair is created before instance
  depends_on = [aws_key_pair.deployer]
}

# Create Elastic IP
resource "aws_eip" "main" {
  instance = aws_instance.main.id
  domain   = "vpc"

  tags = {
    Name = "${var.instance_name}-eip"
  }

  # Ensure instance is created before EIP
  depends_on = [aws_internet_gateway.main]
}
```

### Step 8: Define Outputs

**File: `outputs.tf`**
```hcl
# Instance Details
output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.main.id
}

output "instance_public_ip" {
  description = "Public IP address of the instance"
  value       = aws_eip.main.public_ip
}

output "instance_private_ip" {
  description = "Private IP address of the instance"
  value       = aws_instance.main.private_ip
}

# Network Details
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "subnet_id" {
  description = "ID of the subnet"
  value       = aws_subnet.public.id
}

output "security_group_id" {
  description = "ID of the security group"
  value       = aws_security_group.instance.id
}

# Connection Information
output "ssh_connection_string" {
  description = "SSH connection command"
  value       = "ssh -i ~/.ssh/id_rsa ec2-user@${aws_eip.main.public_ip}"
}

output "web_url" {
  description = "URL to access web server"
  value       = "http://${aws_eip.main.public_ip}"
}

# AMI Information
output "ami_id" {
  description = "AMI ID used for the instance"
  value       = data.aws_ami.amazon_linux_2023.id
}
```

### Step 9: Initialize and Deploy

**Generate SSH key (if you don't have one):**
```bash
ssh-keygen -t rsa -b 4096 -C "your-email@example.com" -f ~/.ssh/id_rsa
```

**Initialize Terraform:**
```bash
terraform init
```

**Expected output:**
```
Initializing the backend...
Initializing provider plugins...
- Finding hashicorp/aws versions matching "~> 5.0"...
- Installing hashicorp/aws v5.40.0...

Terraform has been successfully initialized!
```

**Format code:**
```bash
terraform fmt
```

**Validate configuration:**
```bash
terraform validate
```

**Preview changes:**
```bash
terraform plan
```

**Review the plan carefully:**
- Check resource count (should be ~10 resources)
- Verify AMI ID looks correct
- Check CIDR blocks and security group rules

**Apply configuration:**
```bash
terraform apply
```

Type `yes` when prompted.

**Deployment will take 2-3 minutes.**

### Step 10: Verify and Test

**Check outputs:**
```bash
terraform output

# Get specific output
terraform output instance_public_ip
terraform output ssh_connection_string
```

**SSH into instance:**
```bash
# Use output command
$(terraform output -raw ssh_connection_string)

# Or manually
ssh -i ~/.ssh/id_rsa ec2-user@$(terraform output -raw instance_public_ip)
```

**Test web server:**
```bash
# From your local machine
curl http://$(terraform output -raw instance_public_ip)

# Or open in browser
open http://$(terraform output -raw web_url)
```

**Verify in AWS Console:**
1. Go to EC2 Dashboard
2. Check Instances - you should see your VM running
3. Check VPC - verify VPC, subnet, route table, IGW
4. Check Security Groups - verify rules
5. Check Elastic IPs - verify EIP attached

**Check Terraform state:**
```bash
# List resources in state
terraform state list

# Show specific resource
terraform state show aws_instance.main

# View entire state
terraform show
```

### Step 11: Make Changes (Optional)

**Modify instance type:**

Edit `terraform.tfvars`:
```hcl
instance_type = "t3.small"  # Changed from t2.micro
```

**Plan and apply changes:**
```bash
terraform plan
terraform apply
```

**Note:** This will stop and restart the instance!

### Step 12: Clean Up Resources

**IMPORTANT:** Always clean up to avoid charges!

```bash
# Preview what will be destroyed
terraform plan -destroy

# Destroy all resources
terraform destroy
```

Type `yes` when prompted.

**Verify cleanup:**
```bash
# Check AWS Console - all resources should be gone

# Check Terraform state
terraform show  # Should be empty
```

**Manual verification in AWS Console:**
- EC2: No instances
- VPC: No custom VPCs (default VPC remains)
- Elastic IPs: No allocated IPs
- Key Pairs: Key should be deleted

---

## Success Criteria
- [ ] Terraform successfully initializes
- [ ] Plan shows expected resource creations
- [ ] Apply creates all resources without errors
- [ ] Can SSH into instance using Terraform-managed key
- [ ] Web server responds on port 80
- [ ] Outputs display correct information
- [ ] Destroy removes all resources cleanly

## Extension Ideas
1. **Add Monitoring:** CloudWatch alarms for CPU usage
2. **User Data Enhancement:** Install more packages or deploy app
3. **Multiple Environments:** Use workspaces for dev/staging/prod
4. **Remote State:** Store state in S3 with locking via DynamoDB
5. **Variables File per Environment:** dev.tfvars, prod.tfvars
6. **Add Data Volume:** Attach additional EBS volume
7. **Backup Strategy:** Create AMI snapshot on schedule

## Common Issues & Solutions

**Issue:** "Error: error configuring Terraform AWS Provider"  
**Solution:** Run `aws configure` and verify credentials work with `aws sts get-caller-identity`

**Issue:** "Error: creating EC2 Instance: UnauthorizedOperation"  
**Solution:** IAM user needs EC2 full access permissions

**Issue:** "Error: creating VPC: VpcLimitExceeded"  
**Solution:** Delete unused VPCs or request limit increase

**Issue:** SSH connection refused  
**Solution:** 
- Verify security group allows your IP
- Check instance state is "running"
- Wait 2-3 minutes after creation for SSH to be ready

**Issue:** "Error: Error importing keyPair: InvalidKeyPair.Duplicate"  
**Solution:** Key pair name already exists - change `ssh_key_name` variable or delete existing key in AWS

## Understanding Terraform Workflow

```
terraform init    → Download providers, initialize backend
terraform fmt     → Format code to standard style
terraform validate → Check syntax and configuration
terraform plan    → Preview changes (DRY RUN)
terraform apply   → Create/modify infrastructure
terraform destroy → Delete all managed infrastructure
terraform show    → View current state
terraform output  → Display output values
```

## Cost Estimation

**Resources created:**
- 1x t2.micro EC2 instance: ~$8.50/month (free tier: 750 hours/month)
- 1x 8GB EBS volume: ~$0.80/month
- 1x Elastic IP (attached): FREE
- Data transfer: First 100GB OUT free

**Total monthly cost:** ~$0 (within free tier) or ~$10/month (after free tier)

**Total for this project:** ~$0.10 for a few hours of testing

---

**Completion Time:** 2-3 hours  
**Difficulty:** Beginner  
**AWS Cost:** Free tier eligible  
**Next Project:** Terraform Three-Tier VPC Architecture

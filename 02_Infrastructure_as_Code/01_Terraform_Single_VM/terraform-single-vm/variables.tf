#AWS REGION
variable "aws_region" {
  description = "AWS Region to deploy resources"
  type        = string
  default     = "us-east-2"
}

#Instance Config
variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "instance_name" {
  description = "Name of the EC2 instance"
  type        = string
  default     = "terraform-demo-vm"
}

#Network Config
variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "subnet_cidr" {
  description = "CIDR block for the subnet"
  type        = string
  default     = "10.0.1.0/24"
}

#SSH Config
variable "ssh_key_name" {
  description = "Name of the SSH key pair to use for the EC2 instance"
  type        = string
}

variable "ssh_public_key_path" {
  description = "Path to the SSH public key file"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

#Security
variable "allowed_ssh_cidr" {
  description = "CIDR block allowed to access the EC2 instance via SSH"
  type        = string
  default     = "73.78.131.222/32" #Change this to your IP for Prod
}

# TAGS
variable "project_tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Environment = "Terraform-Demo"
    Project     = "Dev"
    ManagedBy   = "Terraform"
  }
}


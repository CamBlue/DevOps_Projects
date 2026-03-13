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
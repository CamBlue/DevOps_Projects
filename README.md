# DevOps Projects

A collection of hands-on DevOps projects covering Python automation, Infrastructure as Code, and cloud infrastructure. Built to demonstrate real-world skills in AWS, Terraform, Docker, Kubernetes, and CI/CD tooling.

---

## Python Scripting

| # | Project | Description | Key Tools |
|---|---------|-------------|-----------|
| 01 | **AWS Resource Automation** | CLI tool for managing EC2 instances, S3 buckets, and Lambda functions | Python, Boto3, AWS CLI |
| 02 | **Server Health Check** | Real-time server health monitoring with alerting | Python, psutil, smtplib |
| 03 | **Log Parser & Analyzer** | Parses and analyzes application logs for patterns and anomalies | Python, regex, collections |
| 04 | **SSL Certificate Monitor** | Monitors SSL certificate expiration across multiple domains | Python, ssl, socket |
| 05 | **Automated Backup Script** | Automates file and directory backups with scheduling | Python, shutil, schedule |
| 06 | **Kubernetes API Interaction** | Manages Kubernetes clusters — pod orchestration, scaling, and monitoring | Python, kubernetes API |
| 07 | **Custom CLI Tool** | Full-featured AWS management CLI with 38 commands across EC2, EKS, Lambda, ECR, IAM, CloudWatch, and Cost Explorer | Python, Boto3, Click, Rich |
| 08 | **GitHub Repository Auditor** | Audits GitHub repos for security issues, branch protection, and best practices | Python, PyGithub |
| 09 | **AWS Lambda Cost Optimizer** | Identifies and optimizes underutilized Lambda functions to reduce AWS costs | Python, Boto3, Lambda |

## Infrastructure as Code

| # | Project | Description | Key Tools |
|---|---------|-------------|-----------|
| 01 | **Terraform Single VM** | Provisions a single EC2 instance with security groups and SSH access | Terraform, AWS |
| 02 | **Terraform Three-Tier VPC** | Production-grade VPC with public/private subnets, bastion hosts, NAT gateways, and auto scaling groups | Terraform, AWS VPC |

---

## Tech Stack

- **Languages:** Python, Bash, JavaScript, TypeScript
- **Cloud:** AWS (EC2, Lambda, S3, EKS, ECR, CloudWatch, Cost Explorer, VPC)
- **IaC:** Terraform, Ansible
- **Containers:** Docker, Kubernetes
- **CI/CD:** Jenkins, GitHub Actions
- **Monitoring:** CloudWatch, Spectrum, OBM
- **Networking:** TCP/UDP, BGP, IPSec, SSH, SIP, SNMP

---

## Getting Started

Each project is self-contained in its own directory. To run any Python project:

```bash
cd 01_Python_Scripting/<project_folder>
python -m venv venv
source venv/bin/activate      # Linux/Mac
.\venv\Scripts\Activate        # Windows PowerShell
pip install -r requirements.txt
```

For Terraform projects:

```bash
cd 02_Infrastructure_as_Code/<project_folder>
terraform init
terraform plan
terraform apply
```

> **Note:** AWS credentials must be configured via `aws configure` before running any AWS-dependent project.

---

## Author

**Cameron Blue**  
[GitHub](https://github.com/CamBlue) · [Email](mailto:bamclue@gmail.com)

# DevOps Practice Projects - Complete Guide

Welcome to your comprehensive DevOps practice project collection! This repository contains **26 hands-on projects** organized into 4 categories, progressing from beginner to advanced levels.

## 📁 Project Structure

```
DevOps_Practice_Projects/
├── 01_Python_Scripting/          (9 projects)
├── 02_Infrastructure_as_Code/     (8 projects)
├── 03_CICD_Pipelines/             (8 projects)
└── 04_Capstone_Project/           (1 comprehensive project)
```

---

## 🐍 Category 1: Python Scripting for DevOps (9 Projects)

### Beginner Level
1. **AWS Resource Automation** - Boto3 CLI tool for EC2, S3, Lambda management
2. **Server Health Check** - Monitor servers, check endpoints, send alerts
3. **Log Parser & Analyzer** - Parse logs, extract patterns, generate reports
4. **SSL Certificate Monitor** - Track certificate expiry, automated alerts
5. **Automated Backup Script** - Backup databases/files to S3 with rotation

### Intermediate Level  
6. **Kubernetes API Interaction** - Programmatic K8s cluster management
7. **Custom CLI Tool** - Build production CLI with Click framework
8. **GitHub Repository Auditor** - Scan repos for security/compliance issues
9. **AWS Lambda Cost Optimizer** - Automate resource scheduling to reduce costs

**Time Investment:** 20-25 hours total  
**Skills Gained:** Python, Boto3, REST APIs, automation, alerting

---

## 🏗️ Category 2: Infrastructure as Code (8 Projects)

### Terraform Track
1. **Single VM Deployment** - Basic Terraform with EC2, security groups
2. **Three-Tier VPC Architecture** - Production VPC with public/private subnets, ALB, RDS
3. **Modular Infrastructure** - Reusable Terraform modules, remote state
4. **Multi-Environment Setup** - Dev/staging/prod with workspaces

### Ansible Track
5. **Web Server Configuration** - Apache/Nginx setup with playbooks
6. **Application Deployment** - Deploy containerized apps with Ansible
7. **Dynamic Inventory** - AWS EC2 dynamic inventory integration

### Combined
8. **Terraform + Ansible Integration** - Provision with TF, configure with Ansible

**Time Investment:** 25-30 hours total  
**Skills Gained:** Terraform HCL, Ansible playbooks, IaC best practices, AWS architecture

---

## 🔄 Category 3: CI/CD Pipelines (8 Projects)

### Beginner Level
1. **Basic Build-Test-Deploy** - GitHub Actions pipeline basics
2. **Jenkins Pipeline with GitHub** - Jenkins + GitHub webhooks integration

### Intermediate Level
3. **Full End-to-End Pipeline** - Complete pipeline with security scanning, staging
4. **GitOps with ArgoCD** - Kubernetes GitOps deployment automation
5. **Terraform in CI/CD** - Automated infrastructure changes via pipelines

### Advanced Level
6. **Microservice Deployment** - Multi-service apps with separate pipelines
7. **Monitoring Stack Integration** - Prometheus + Grafana in CI/CD
8. **Self-Hosted Runners** - Custom GitHub Actions runners on AWS

**Time Investment:** 25-30 hours total  
**Skills Gained:** GitHub Actions, Jenkins, GitOps, container orchestration, monitoring

---

## 🎯 Category 4: Capstone Project

**Full-Stack DevOps Project** - Combines all three skill areas:
- Python Flask/FastAPI application with tests
- Terraform + Ansible infrastructure provisioning
- Complete CI/CD pipeline with GitHub Actions
- Monitoring with Prometheus + Grafana
- Production-ready documentation

**Time Investment:** 15-20 hours  
**Skills Gained:** End-to-end DevOps workflow, production thinking, portfolio project

---

## 🎓 Recommended Learning Path

### Path 1: Structured Approach (Beginner)
Follow in order 1 → 2 → 3 → 4, completing all projects in each category before moving on.

**Timeline:** 12-14 weeks (5-7 hours/week)

### Path 2: Skill-Focused (Intermediate)
Pick projects based on current gaps:
- Need Python? → Category 1
- Need IaC? → Category 2  
- Need CI/CD? → Category 3

**Timeline:** 8-10 weeks (focused learning)

### Path 3: Portfolio Sprint (Interview Prep)
Build these 5 showcase projects:
1. AWS Resource Automation (Python)
2. Three-Tier VPC Architecture (Terraform)
3. Terraform + Ansible Combined (IaC)
4. Full End-to-End Pipeline (CI/CD)
5. Capstone Project (All skills)

**Timeline:** 6-8 weeks (intensive)

---

## 📊 Difficulty Distribution

| Level | Python | IaC | CI/CD | Total |
|-------|--------|-----|-------|-------|
| Beginner | 5 | 4 | 2 | 11 |
| Intermediate | 3 | 3 | 3 | 9 |
| Advanced | 1 | 1 | 3 | 5 |
| Capstone | - | - | - | 1 |

---

## 🛠️ Prerequisites

### Required
- Python 3.8+ installed
- Git installed
- AWS account (free tier sufficient)
- GitHub account
- Text editor or IDE

### Recommended
- Basic Linux command line knowledge
- Understanding of networking basics
- Familiarity with Git workflows
- AWS CLI installed and configured

---

## 💡 How to Use This Repository

### For Each Project:

1. **Read the guide.md** in the project folder
2. **Check prerequisites** - install required tools
3. **Follow step-by-step instructions** - don't skip steps
4. **Test thoroughly** - verify each component works
5. **Clean up resources** - avoid AWS charges
6. **Document your work** - add to your GitHub portfolio

### Success Metrics:

- [ ] All code runs without errors
- [ ] Can explain what each component does
- [ ] Passed all success criteria in the guide
- [ ] Uploaded to GitHub with good README
- [ ] Can demo the project in an interview setting

---

## 📚 Additional Resources

### Python for DevOps
- [Real Python](https://realpython.com/)
- [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [Click Documentation](https://click.palletsprojects.com/)

### Infrastructure as Code
- [Terraform Documentation](https://www.terraform.io/docs)
- [Ansible Documentation](https://docs.ansible.com/)
- [LocalStack](https://localstack.cloud/) - Test Terraform locally

### CI/CD
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Jenkins Documentation](https://www.jenkins.io/doc/)
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)

### Practice Platforms
- [KillerCoda](https://killercoda.com/) - Free DevOps labs
- [KodeKloud](https://kodekloud.com/) - Hands-on learning
- [SadServers](https://sadservers.com/) - Troubleshooting practice

---

## 🎯 Your DevOps Journey

```
Week 1-2:   Python automation basics (Projects 1-3)
Week 3-4:   Advanced Python + monitoring (Projects 4-7)
Week 5-6:   Terraform fundamentals (Projects 1-3)
Week 7-8:   Ansible + combined IaC (Projects 4-8)
Week 9-10:  CI/CD basics (Projects 1-3)
Week 11-12: Advanced pipelines (Projects 4-8)
Week 13-14: Capstone integration project
```

By the end, you'll have:
- **26 completed projects** on your GitHub
- **Portfolio-ready** showcase work
- **Interview preparation** with hands-on experience
- **Production skills** for DevOps roles

---

## ⚠️ Important Notes

### AWS Costs
- Always use free tier eligible resources
- Set up billing alerts
- Clean up resources after each project
- Use LocalStack for local testing when possible

### Security
- Never commit credentials to Git
- Use environment variables for secrets
- Follow least-privilege IAM principles
- Rotate access keys regularly

### Best Practices
- Write good README files
- Comment your code
- Use version control (Git)
- Test before production
- Document your learning

---

## 🚀 Getting Started

Ready to begin? Start here:

1. **Clone or download this repository**
2. **Read through this README completely**
3. **Choose your learning path** (1, 2, or 3 above)
4. **Set up your environment** (Python, AWS CLI, Git)
5. **Begin with Project 01_01** (AWS Resource Automation)

Good luck on your DevOps journey! 🎉

---

**Last Updated:** March 2026  
**Total Projects:** 26  
**Estimated Completion Time:** 85-105 hours  
**Target Role:** Junior DevOps Engineer / DevOps Associate

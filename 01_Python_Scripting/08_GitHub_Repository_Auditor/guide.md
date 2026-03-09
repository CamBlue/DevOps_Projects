# GitHub Repository Auditor

## Project Overview
**Difficulty:** Intermediate  
**Estimated Time:** 3-4 hours  
**Skills Practiced:** Python, GitHub API, Security Auditing, REST APIs

### What You'll Build
A Python tool that audits GitHub repositories for:
- Security vulnerabilities and exposed secrets
- Stale branches and inactive contributors
- Missing required files (README, LICENSE, .gitignore)
- Branch protection rules compliance
- Repository configuration best practices
- Dependency vulnerabilities
- Code quality metrics

### Why This Matters
Repository auditing is crucial for security and compliance. This project teaches you to automate security checks and organizational standards—preventing issues before they reach production.

### Prerequisites
- Python 3.8+ installed
- GitHub account with personal access token
- Basic understanding of Git and GitHub concepts

---

## Step-by-Step Implementation

### Step 1: Create GitHub Personal Access Token

**Navigate to GitHub:**
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Give it a descriptive name: "Repository Auditor"
4. Select scopes:
   - ✓ `repo` (all)
   - ✓ `read:org`
   - ✓ `read:user`
5. Click "Generate token"
6. **IMPORTANT:** Copy token immediately (you won't see it again)

**Store token securely:**
```bash
# Create .env file
echo "GITHUB_TOKEN=your_token_here" > .env
echo ".env" >> .gitignore
```

### Step 2: Project Setup
```bash
mkdir github-auditor
cd github-auditor
python3 -m venv venv
source venv/bin/activate
pip install PyGithub requests python-dotenv tabulate
```

### Step 3: Initialize GitHub Client

Create `github_auditor.py`:
```python
from github import Github
from github.GithubException import GithubException
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

class GitHubAuditor:
    def __init__(self, token=None):
        """Initialize GitHub client"""
        self.token = token or os.getenv('GITHUB_TOKEN')
        if not self.token:
            raise ValueError("GitHub token required")

        self.github = Github(self.token)
        self.user = self.github.get_user()
        print(f"✓ Authenticated as: {self.user.login}")

    def get_repository(self, repo_name):
        """Get repository by name (owner/repo format)"""
        try:
            return self.github.get_repo(repo_name)
        except GithubException as e:
            print(f"✗ Error accessing repository: {e}")
            return None
```

### Step 4: Audit Security Issues

```python
def audit_security(self, repo):
    """Audit repository for security issues"""
    issues = []

    # Check if repository is private
    if not repo.private:
        issues.append({
            'severity': 'INFO',
            'category': 'Visibility',
            'message': 'Repository is public'
        })

    # Check for vulnerability alerts (requires security scope)
    try:
        if repo.get_vulnerability_alert():
            issues.append({
                'severity': 'HIGH',
                'category': 'Security',
                'message': 'Vulnerability alerts enabled and active'
            })
    except:
        pass

    # Check for security policy
    try:
        repo.get_contents("SECURITY.md")
    except:
        issues.append({
            'severity': 'MEDIUM',
            'category': 'Security',
            'message': 'Missing SECURITY.md file'
        })

    # Check for .gitignore
    try:
        repo.get_contents(".gitignore")
    except:
        issues.append({
            'severity': 'MEDIUM',
            'category': 'Security',
            'message': 'Missing .gitignore file (risk of committing secrets)'
        })

    # Check for exposed secrets in recent commits
    secrets_found = self.scan_for_secrets(repo)
    if secrets_found:
        issues.append({
            'severity': 'CRITICAL',
            'category': 'Security',
            'message': f'Potential secrets found in code: {", ".join(secrets_found)}'
        })

    return issues

def scan_for_secrets(self, repo, max_commits=10):
    """Scan recent commits for potential secrets"""
    import re

    patterns = {
        'AWS Key': r'AKIA[0-9A-Z]{16}',
        'API Key': r'api[_-]?key["\'\s:=]+[a-zA-Z0-9_-]{20,}',
        'Private Key': r'-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----',
        'Password': r'password["\'\s:=]+[^\s]{8,}',
        'Token': r'token["\'\s:=]+[a-zA-Z0-9_-]{20,}'
    }

    found_secrets = []
    commits = list(repo.get_commits()[:max_commits])

    for commit in commits:
        for file in commit.files:
            if file.patch:
                for secret_type, pattern in patterns.items():
                    if re.search(pattern, file.patch, re.IGNORECASE):
                        found_secrets.append(f"{secret_type} in {file.filename}")

    return found_secrets
```

### Step 5: Audit Branch Management

```python
def audit_branches(self, repo):
    """Audit branch management"""
    issues = []
    branches = list(repo.get_branches())

    # Check for stale branches
    stale_days = 90
    stale_branches = []

    for branch in branches:
        commit = repo.get_commit(branch.commit.sha)
        days_old = (datetime.now() - commit.commit.author.date.replace(tzinfo=None)).days

        if days_old > stale_days and branch.name != repo.default_branch:
            stale_branches.append(f"{branch.name} ({days_old} days old)")

    if stale_branches:
        issues.append({
            'severity': 'LOW',
            'category': 'Branches',
            'message': f'{len(stale_branches)} stale branches: {", ".join(stale_branches[:3])}'
        })

    # Check default branch protection
    default_branch = repo.get_branch(repo.default_branch)
    if not default_branch.protected:
        issues.append({
            'severity': 'HIGH',
            'category': 'Branches',
            'message': f'Default branch "{repo.default_branch}" is not protected'
        })
    else:
        # Check protection rules
        protection = default_branch.get_protection()

        if not protection.required_pull_request_reviews:
            issues.append({
                'severity': 'MEDIUM',
                'category': 'Branches',
                'message': 'Pull request reviews not required'
            })

        if not protection.enforce_admins.enabled:
            issues.append({
                'severity': 'LOW',
                'category': 'Branches',
                'message': 'Branch protection not enforced for admins'
            })

    return issues
```

### Step 6: Audit Repository Configuration

```python
def audit_configuration(self, repo):
    """Audit repository configuration and best practices"""
    issues = []

    # Check for required files
    required_files = {
        'README.md': 'HIGH',
        'LICENSE': 'MEDIUM',
        'CONTRIBUTING.md': 'LOW',
        '.github/CODEOWNERS': 'LOW'
    }

    for file_path, severity in required_files.items():
        try:
            repo.get_contents(file_path)
        except:
            issues.append({
                'severity': severity,
                'category': 'Documentation',
                'message': f'Missing {file_path}'
            })

    # Check if repository has description
    if not repo.description:
        issues.append({
            'severity': 'LOW',
            'category': 'Metadata',
            'message': 'Repository has no description'
        })

    # Check if repository has topics/tags
    if not repo.get_topics():
        issues.append({
            'severity': 'LOW',
            'category': 'Metadata',
            'message': 'Repository has no topics/tags'
        })

    # Check if issues are enabled
    if not repo.has_issues:
        issues.append({
            'severity': 'INFO',
            'category': 'Configuration',
            'message': 'Issues are disabled'
        })

    # Check if wiki is enabled but empty
    if repo.has_wiki:
        issues.append({
            'severity': 'INFO',
            'category': 'Configuration',
            'message': 'Wiki is enabled'
        })

    return issues
```

### Step 7: Audit Contributors and Activity

```python
def audit_contributors(self, repo):
    """Audit contributor activity"""
    issues = []

    # Get contributors
    contributors = list(repo.get_contributors())

    if len(contributors) == 1:
        issues.append({
            'severity': 'INFO',
            'category': 'Collaboration',
            'message': 'Repository has only one contributor'
        })

    # Check for inactive contributors
    commits = list(repo.get_commits()[:50])
    recent_authors = set()

    for commit in commits:
        if commit.author:
            recent_authors.add(commit.author.login)

    inactive_contributors = [c.login for c in contributors if c.login not in recent_authors]

    if len(inactive_contributors) > 0:
        issues.append({
            'severity': 'INFO',
            'category': 'Collaboration',
            'message': f'{len(inactive_contributors)} inactive contributors: {", ".join(inactive_contributors[:3])}'
        })

    # Check last commit date
    latest_commit = commits[0]
    days_since_commit = (datetime.now() - latest_commit.commit.author.date.replace(tzinfo=None)).days

    if days_since_commit > 180:
        issues.append({
            'severity': 'MEDIUM',
            'category': 'Activity',
            'message': f'No commits in {days_since_commit} days (repository may be abandoned)'
        })

    return issues
```

### Step 8: Generate Audit Report

```python
def generate_report(self, repo):
    """Generate comprehensive audit report"""
    print(f"\n{'='*80}")
    print(f"GitHub Repository Audit Report")
    print(f"Repository: {repo.full_name}")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")

    # Run all audits
    all_issues = []

    print("🔒 Auditing security...")
    all_issues.extend(self.audit_security(repo))

    print("🌿 Auditing branches...")
    all_issues.extend(self.audit_branches(repo))

    print("⚙️  Auditing configuration...")
    all_issues.extend(self.audit_configuration(repo))

    print("👥 Auditing contributors...")
    all_issues.extend(self.audit_contributors(repo))

    # Categorize by severity
    critical = [i for i in all_issues if i['severity'] == 'CRITICAL']
    high = [i for i in all_issues if i['severity'] == 'HIGH']
    medium = [i for i in all_issues if i['severity'] == 'MEDIUM']
    low = [i for i in all_issues if i['severity'] == 'LOW']
    info = [i for i in all_issues if i['severity'] == 'INFO']

    # Display summary
    print(f"\n{'='*80}")
    print("Summary")
    print(f"{'='*80}")
    print(f"🔴 Critical: {len(critical)}")
    print(f"🟠 High:     {len(high)}")
    print(f"🟡 Medium:   {len(medium)}")
    print(f"🟢 Low:      {len(low)}")
    print(f"ℹ️  Info:     {len(info)}")
    print(f"\nTotal Issues: {len(all_issues)}")

    # Display issues by severity
    for severity_name, severity_issues in [
        ('CRITICAL', critical),
        ('HIGH', high),
        ('MEDIUM', medium),
        ('LOW', low),
        ('INFO', info)
    ]:
        if severity_issues:
            print(f"\n{severity_name} Issues:")
            print("-" * 80)
            for issue in severity_issues:
                print(f"  [{issue['category']}] {issue['message']}")

    return all_issues
```

### Step 9: Add CLI Interface

```python
import argparse
import json

def main():
    parser = argparse.ArgumentParser(description='GitHub Repository Auditor')
    parser.add_argument('repository', help='Repository in format owner/repo')
    parser.add_argument('--token', help='GitHub personal access token')
    parser.add_argument('--export-json', help='Export results to JSON file')

    args = parser.parse_args()

    try:
        auditor = GitHubAuditor(token=args.token)
        repo = auditor.get_repository(args.repository)

        if not repo:
            print("Failed to access repository")
            return

        issues = auditor.generate_report(repo)

        # Export if requested
        if args.export_json:
            with open(args.export_json, 'w') as f:
                json.dump(issues, f, indent=2, default=str)
            print(f"\n✓ Report exported to {args.export_json}")

    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    main()
```

### Step 10: Test Your Implementation

```bash
# Audit a public repository
python github_auditor.py octocat/Hello-World

# Audit your own repository
python github_auditor.py yourusername/your-repo

# Audit with custom token
python github_auditor.py owner/repo --token ghp_your_token_here

# Export results to JSON
python github_auditor.py owner/repo --export-json audit_results.json
```

**Test with your own repositories:**
```bash
# List your repositories
python -c "from github import Github; import os; g = Github(os.getenv('GITHUB_TOKEN')); [print(r.full_name) for r in g.get_user().get_repos()[:10]]"

# Then audit one
python github_auditor.py yourusername/your-repo-name
```

---

## Success Criteria
- [ ] Successfully authenticates with GitHub API
- [ ] Scans repositories for security issues
- [ ] Identifies stale branches and protection issues
- [ ] Checks for required documentation files
- [ ] Analyzes contributor activity
- [ ] Generates comprehensive report
- [ ] Exports results to JSON

## Extension Ideas
1. **Batch Auditing:** Audit all repositories in an organization
2. **Scheduled Scans:** Run audits weekly and track changes
3. **Slack Integration:** Send alerts for critical issues
4. **Auto-Fix:** Automatically create issues for problems found
5. **Dependency Scanning:** Check for outdated dependencies
6. **License Compliance:** Verify license compatibility
7. **Code Quality:** Integrate with CodeClimate or SonarQube

## Common Issues

**Issue:** "Bad credentials" error  
**Solution:** Verify token is correct and has required scopes

**Issue:** "Resource not accessible by integration"  
**Solution:** Token needs `repo` scope for private repositories

**Issue:** Rate limit exceeded  
**Solution:** GitHub API has rate limits; add delays or use authenticated requests

---

**Completion Time:** 3-4 hours  
**Difficulty:** Intermediate  
**Next Project:** AWS Lambda Cost Optimizer

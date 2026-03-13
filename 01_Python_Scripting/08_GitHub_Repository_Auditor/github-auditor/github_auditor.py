import os
import re
import json
import argparse
from datetime import datetime
from github import Github, GithubException, Auth
from dotenv import load_dotenv

load_dotenv()


class GitHubAuditor:
    def __init__(self, token=None):
        """Initialize GitHub client"""
        self.token = token or os.getenv('GITHUB_TOKEN')
        if not self.token:
            raise ValueError("GitHub token required")

        self.github = Github(auth=Auth.Token(self.token))
        self.user = self.github.get_user()
        print(f"✓ Authenticated as: {self.user.login}")

    def get_repository(self, repo_name):
        """Get repository by name (owner/repo format)"""
        try:
            return self.github.get_repo(repo_name)
        except GithubException as e:
            print(f"✗ Error accessing repository: {e}")
            return None

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
            try:
                protection = default_branch.get_protection()

                if not protection.required_pull_request_reviews:
                    issues.append({
                        'severity': 'MEDIUM',
                        'category': 'Branches',
                        'message': 'Pull request reviews not required'
                    })

                enforce_admins = protection.enforce_admins
                if isinstance(enforce_admins, bool):
                    admin_enforced = enforce_admins
                else:
                    admin_enforced = enforce_admins.enabled

                if not admin_enforced:
                    issues.append({
                        'severity': 'LOW',
                        'category': 'Branches',
                        'message': 'Branch protection not enforced for admins'
                    })
            except GithubException:
                issues.append({
                    'severity': 'INFO',
                    'category': 'Branches',
                    'message': 'Could not read branch protection details (may require admin access)'
                })

        return issues

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
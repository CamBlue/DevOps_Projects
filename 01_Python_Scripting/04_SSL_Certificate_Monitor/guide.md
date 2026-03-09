# SSL Certificate Expiry Monitor

## Project Overview
**Difficulty:** Beginner  
**Estimated Time:** 2 hours  
**Skills Practiced:** Python, SSL/TLS, Networking, Alerting

### What You'll Build
A Python script that:
- Checks SSL/TLS certificates for multiple domains
- Extracts certificate expiry dates and details
- Calculates days until expiration
- Sends alerts when certificates are expiring soon
- Generates certificate inventory report

### Why This Matters
SSL certificate expiration causes production outages. This project teaches you to proactively monitor certificates and automate renewal reminders—preventing downtime before it happens.

### Prerequisites
- Python 3.8+ installed
- Basic understanding of SSL/TLS certificates
- List of domains to monitor

---

## Step-by-Step Implementation

### Step 1: Project Setup
```bash
mkdir ssl-monitor
cd ssl-monitor
python3 -m venv venv
source venv/bin/activate
pip install python-dotenv requests
```

### Step 2: Create Project Structure
```
ssl-monitor/
├── ssl_checker.py
├── domains.txt
├── .env
├── requirements.txt
└── README.md
```

### Step 3: Implement SSL Certificate Checker

Create `ssl_checker.py`:
```python
import ssl
import socket
from datetime import datetime, timedelta
import OpenSSL

class SSLChecker:
    def __init__(self, hostname, port=443):
        self.hostname = hostname
        self.port = port

    def get_certificate(self):
        context = ssl.create_default_context()

        try:
            with socket.create_connection((self.hostname, self.port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=self.hostname) as ssock:
                    cert_der = ssock.getpeercert(binary_form=True)
                    cert = OpenSSL.crypto.load_certificate(
                        OpenSSL.crypto.FILETYPE_ASN1, cert_der
                    )
                    return cert
        except Exception as e:
            print(f"✗ Error checking {self.hostname}: {e}")
            return None

    def get_cert_info(self):
        cert = self.get_certificate()
        if not cert:
            return None

        # Extract expiry date
        expiry_date_str = cert.get_notAfter().decode('utf-8')
        expiry_date = datetime.strptime(expiry_date_str, '%Y%m%d%H%M%SZ')

        # Calculate days until expiry
        days_remaining = (expiry_date - datetime.now()).days

        return {
            'hostname': self.hostname,
            'issuer': cert.get_issuer().CN,
            'subject': cert.get_subject().CN,
            'expiry_date': expiry_date,
            'days_remaining': days_remaining,
            'status': self.get_status(days_remaining)
        }

    def get_status(self, days_remaining):
        if days_remaining < 0:
            return 'EXPIRED'
        elif days_remaining < 7:
            return 'CRITICAL'
        elif days_remaining < 30:
            return 'WARNING'
        else:
            return 'OK'
```

### Step 4: Add Bulk Domain Checking

```python
def check_multiple_domains(domains_file):
    results = []

    with open(domains_file, 'r') as f:
        domains = [line.strip() for line in f if line.strip()]

    print(f"🔍 Checking {len(domains)} domains...\n")

    for domain in domains:
        print(f"Checking {domain}...", end=' ')
        checker = SSLChecker(domain)
        info = checker.get_cert_info()

        if info:
            results.append(info)
            status_emoji = {
                'OK': '✓',
                'WARNING': '⚠️',
                'CRITICAL': '🔥',
                'EXPIRED': '❌'
            }
            print(f"{status_emoji[info['status']]} {info['status']}")
        else:
            print("✗ FAILED")

    return results
```

### Step 5: Generate Report

```python
def generate_report(results):
    print("\n" + "="*80)
    print(" SSL Certificate Status Report")
    print("="*80 + "\n")

    # Sort by days remaining
    results.sort(key=lambda x: x['days_remaining'])

    for result in results:
        print(f"Domain: {result['hostname']}")
        print(f"  Subject: {result['subject']}")
        print(f"  Issuer: {result['issuer']}")
        print(f"  Expiry: {result['expiry_date'].strftime('%Y-%m-%d')}")
        print(f"  Days Remaining: {result['days_remaining']}")
        print(f"  Status: {result['status']}")
        print()

    # Summary
    status_counts = {}
    for result in results:
        status = result['status']
        status_counts[status] = status_counts.get(status, 0) + 1

    print("Summary:")
    for status, count in status_counts.items():
        print(f"  {status}: {count}")
```

### Step 6: Add Alerting

```python
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def send_alert(result):
    if result['status'] in ['CRITICAL', 'EXPIRED']:
        send_slack_alert(result)

def send_slack_alert(result):
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    if not webhook_url:
        return

    message = {
        "text": f"🚨 SSL Certificate Alert",
        "attachments": [{
            "color": "danger",
            "fields": [
                {"title": "Domain", "value": result['hostname']},
                {"title": "Status", "value": result['status']},
                {"title": "Days Remaining", "value": str(result['days_remaining'])},
                {"title": "Expiry Date", "value": result['expiry_date'].strftime('%Y-%m-%d')}
            ]
        }]
    }

    try:
        requests.post(webhook_url, json=message)
    except Exception as e:
        print(f"Failed to send alert: {e}")
```

### Step 7: Create domains.txt

```
example.com
google.com
github.com
aws.amazon.com
```

### Step 8: Add CLI Interface

```python
import argparse

def main():
    parser = argparse.ArgumentParser(description='SSL Certificate Monitor')
    parser.add_argument('--domains', default='domains.txt', help='File with domain list')
    parser.add_argument('--alert', action='store_true', help='Send alerts for expiring certs')
    parser.add_argument('--threshold', type=int, default=30, help='Alert threshold in days')

    args = parser.parse_args()

    results = check_multiple_domains(args.domains)
    generate_report(results)

    if args.alert:
        for result in results:
            if result['days_remaining'] < args.threshold:
                send_alert(result)

if __name__ == "__main__":
    main()
```

### Step 9: Test Your Implementation

```bash
# Check domains
python ssl_checker.py

# With custom threshold
python ssl_checker.py --alert --threshold 60
```

### Step 10: Schedule Regular Checks

**Using cron (Linux/Mac):**
```bash
# Check daily at 9 AM
0 9 * * * /path/to/venv/bin/python /path/to/ssl_checker.py --alert
```

**Using Windows Task Scheduler:** Create scheduled task to run daily

---

## Success Criteria
- [ ] Successfully retrieves SSL certificates from domains
- [ ] Correctly calculates days until expiration
- [ ] Identifies expired, critical, and warning status certificates
- [ ] Sends alerts for certificates expiring soon
- [ ] Generates clear status report

## Extension Ideas
1. **CSV Export:** Export certificate inventory to CSV
2. **Email Alerts:** Add email notification option
3. **Historical Tracking:** Store results in SQLite database
4. **Wildcard Support:** Check multiple subdomains
5. **Certificate Chain:** Validate entire certificate chain
6. **Auto-Renewal:** Integrate with Let's Encrypt for auto-renewal

---

**Completion Time:** 2 hours  
**Difficulty:** Beginner  
**Next Project:** Automated Backup Script

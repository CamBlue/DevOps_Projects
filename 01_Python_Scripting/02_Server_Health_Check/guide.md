# Server Health Check Script

## Project Overview
**Difficulty:** Beginner  
**Estimated Time:** 2-3 hours  
**Skills Practiced:** Python, System Monitoring, REST APIs, Alerting

### What You'll Build
A Python script that monitors server health by:
- Pinging servers to check availability
- Checking HTTP/HTTPS endpoint status codes
- Monitoring system resources (CPU, memory, disk usage)
- Sending alerts via Slack/Email when thresholds are exceeded
- Generating health check reports

### Why This Matters
Server monitoring is a fundamental DevOps responsibility. This project teaches you how to programmatically check system health, detect issues before they become critical, and automate alerting—skills used daily in production environments.

### Prerequisites
- Python 3.8+ installed
- Basic understanding of HTTP status codes
- (Optional) Slack workspace for alert testing
- (Optional) SMTP credentials for email alerts

---

## Step-by-Step Implementation

### Step 1: Project Setup
```bash
mkdir server-health-monitor
cd server-health-monitor
python3 -m venv venv
source venv/bin/activate
pip install requests psutil python-dotenv
```

**Package Purposes:**
- `requests` - HTTP requests to check endpoints
- `psutil` - System resource monitoring (CPU, memory, disk)
- `python-dotenv` - Load environment variables from .env file

### Step 2: Create Project Structure
```
server-health-monitor/
├── health_checker.py
├── alerting.py
├── config.py
├── servers.yaml
├── .env
├── requirements.txt
└── README.md
```

```bash
touch health_checker.py alerting.py config.py servers.yaml .env requirements.txt README.md
```

### Step 3: Define Server Configuration

Create `servers.yaml`:
```yaml
servers:
  - name: "Production API"
    url: "https://api.example.com/health"
    type: "http"
    expected_status: 200
    timeout: 5

  - name: "Database Server"
    host: "db.example.com"
    port: 5432
    type: "tcp"

  - name: "Web Server"
    url: "https://www.example.com"
    type: "http"
    expected_status: 200
    timeout: 10

  - name: "Local Machine"
    type: "system"
    thresholds:
      cpu_percent: 80
      memory_percent: 85
      disk_percent: 90

alerts:
  slack_webhook: "${SLACK_WEBHOOK_URL}"
  email_enabled: true
  email_to: "bamclueaws@gmail.com"
```

### Step 4: Implement Health Check Functions

Create `health_checker.py`:

**Core Functions to Implement:**

1. **HTTP Health Check:**
```python
import requests
from datetime import datetime

def check_http_endpoint(url, expected_status=200, timeout=5):
    try:
        start_time = datetime.now()
        response = requests.get(url, timeout=timeout)
        response_time = (datetime.now() - start_time).total_seconds()

        status = "HEALTHY" if response.status_code == expected_status else "UNHEALTHY"

        return {
            'status': status,
            'status_code': response.status_code,
            'response_time': response_time,
            'timestamp': datetime.now().isoformat()
        }
    except requests.exceptions.Timeout:
        return {'status': 'UNHEALTHY', 'error': 'Timeout'}
    except requests.exceptions.ConnectionError:
        return {'status': 'UNHEALTHY', 'error': 'Connection Failed'}
    except Exception as e:
        return {'status': 'UNHEALTHY', 'error': str(e)}
```

2. **TCP Port Check:**
```python
import socket

def check_tcp_port(host, port, timeout=5):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()

        if result == 0:
            return {'status': 'HEALTHY', 'port_open': True}
        else:
            return {'status': 'UNHEALTHY', 'port_open': False}
    except Exception as e:
        return {'status': 'UNHEALTHY', 'error': str(e)}
```

3. **System Resource Check:**
```python
import psutil

def check_system_resources(thresholds):
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    issues = []

    if cpu_percent > thresholds.get('cpu_percent', 80):
        issues.append(f"High CPU usage: {cpu_percent}%")

    if memory.percent > thresholds.get('memory_percent', 85):
        issues.append(f"High memory usage: {memory.percent}%")

    if disk.percent > thresholds.get('disk_percent', 90):
        issues.append(f"High disk usage: {disk.percent}%")

    status = "HEALTHY" if not issues else "UNHEALTHY"

    return {
        'status': status,
        'cpu_percent': cpu_percent,
        'memory_percent': memory.percent,
        'disk_percent': disk.percent,
        'issues': issues
    }
```

4. **Main Health Check Orchestrator:**
```python
import yaml

def load_config(config_file='servers.yaml'):
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)

def run_health_checks(config):
    results = []

    for server in config['servers']:
        print(f"Checking {server['name']}...")

        if server['type'] == 'http':
            result = check_http_endpoint(
                server['url'], 
                server.get('expected_status', 200),
                server.get('timeout', 5)
            )
        elif server['type'] == 'tcp':
            result = check_tcp_port(
                server['host'],
                server['port'],
                server.get('timeout', 5)
            )
        elif server['type'] == 'system':
            result = check_system_resources(server.get('thresholds', {}))

        result['server_name'] = server['name']
        results.append(result)

    return results
```

### Step 5: Implement Alerting

Create `alerting.py`:

**Slack Alert Function:**
```python
import requests
import json

def send_slack_alert(webhook_url, message, server_name, status):
    color = "danger" if status == "UNHEALTHY" else "good"

    payload = {
        "attachments": [{
            "color": color,
            "title": f"🚨 Server Alert: {server_name}",
            "text": message,
            "footer": "Health Check Monitor",
            "ts": int(time.time())
        }]
    }

    try:
        response = requests.post(webhook_url, json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"Failed to send Slack alert: {e}")
        return False
```

**Email Alert Function:**
```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email_alert(smtp_config, to_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = smtp_config['username']
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'html'))

    try:
        with smtplib.SMTP(smtp_config['server'], smtp_config['port']) as server:
            server.starttls()
            server.login(smtp_config['username'], smtp_config['password'])
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
```

**Alert Decision Logic:**
```python
def process_alerts(results, config):
    unhealthy_servers = [r for r in results if r['status'] == 'UNHEALTHY']

    if not unhealthy_servers:
        print("✓ All servers healthy")
        return

    for server in unhealthy_servers:
        message = f"Server {server['server_name']} is unhealthy!\n"
        message += f"Details: {server.get('error', 'Unknown issue')}"

        # Send Slack alert
        if config['alerts'].get('slack_webhook'):
            send_slack_alert(
                config['alerts']['slack_webhook'],
                message,
                server['server_name'],
                server['status']
            )

        # Send email alert
        if config['alerts'].get('email_enabled'):
            send_email_alert(
                config['alerts']['smtp'],
                config['alerts']['email_to'],
                f"Health Check Alert: {server['server_name']}",
                message
            )
```

### Step 6: Environment Variables

Create `.env` file:
```env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

**Load environment variables:**
```python
from dotenv import load_dotenv
import os

load_dotenv()

# Replace placeholders in config
def load_env_config(config):
    if '${SLACK_WEBHOOK_URL}' in str(config):
        config['alerts']['slack_webhook'] = os.getenv('SLACK_WEBHOOK_URL')
    return config
```

### Step 7: Add Reporting

**Generate HTML Report:**
```python
from datetime import datetime

def generate_html_report(results):
    html = f'''
    <html>
    <head><title>Health Check Report</title></head>
    <body>
        <h1>Server Health Report</h1>
        <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        <table border="1">
            <tr>
                <th>Server</th>
                <th>Status</th>
                <th>Details</th>
            </tr>
    '''

    for result in results:
        status_color = "green" if result['status'] == "HEALTHY" else "red"
        html += f'''
            <tr>
                <td>{result['server_name']}</td>
                <td style="color: {status_color};">{result['status']}</td>
                <td>{result.get('error', 'OK')}</td>
            </tr>
        '''

    html += '''
        </table>
    </body>
    </html>
    '''

    with open(f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html", 'w') as f:
        f.write(html)
```

### Step 8: Create Main Script

**Complete `health_checker.py` main function:**
```python
def main():
    print("🏥 Starting Health Check Monitor...\n")

    # Load configuration
    config = load_config('servers.yaml')
    config = load_env_config(config)

    # Run health checks
    results = run_health_checks(config)

    # Display results
    print("\n📊 Health Check Results:")
    print("-" * 60)
    for result in results:
        status_emoji = "✓" if result['status'] == "HEALTHY" else "✗"
        print(f"{status_emoji} {result['server_name']}: {result['status']}")

    # Process alerts
    process_alerts(results, config)

    # Generate report
    generate_html_report(results)

    print("\n✓ Health check complete!")

if __name__ == "__main__":
    main()
```

### Step 9: Add Scheduling (Optional)

**Run checks every 5 minutes:**
```python
import time
import schedule

def job():
    main()

# Schedule checks
schedule.every(5).minutes.do(job)

print("🕐 Health monitor running. Press Ctrl+C to stop.")
while True:
    schedule.run_pending()
    time.sleep(1)
```

Install scheduler:
```bash
pip install schedule
```

### Step 10: Test Your Implementation

**Test with local endpoints:**
```bash
# Test against public APIs
python health_checker.py
```

**Test with intentionally failing endpoint:**
```yaml
- name: "Failing Test"
  url: "https://httpstat.us/500"  # Returns 500 error
  type: "http"
  expected_status: 200
```

**Test system monitoring:**
```python
# Create artificial load to test thresholds
import multiprocessing

def cpu_stress():
    while True:
        pass

# Run for 10 seconds to trigger CPU alert
processes = [multiprocessing.Process(target=cpu_stress) for _ in range(4)]
for p in processes:
    p.start()

# Run health check while CPU is stressed
```

---

## Success Criteria
- [ ] Script successfully checks HTTP endpoints and returns status codes
- [ ] TCP port checking works for database/service ports
- [ ] System resource monitoring detects high CPU/memory/disk usage
- [ ] Slack alerts successfully sent for unhealthy servers
- [ ] HTML reports generated with timestamp
- [ ] Error handling for timeouts and connection failures

## Extension Ideas
1. **Database Health:** Add MySQL/PostgreSQL connection checks
2. **SSL Certificate Expiry:** Check SSL cert validity and expiration dates
3. **Response Time Tracking:** Store historical response times in SQLite
4. **Dashboard:** Build Flask web UI to visualize health status
5. **Multi-Region:** Check servers in different AWS regions
6. **Kubernetes:** Check pod health via Kubernetes API
7. **Grafana Integration:** Export metrics to Prometheus/Grafana

## Common Issues & Troubleshooting

**Issue:** SSL certificate verification errors  
**Solution:** Add `verify=False` to requests (only for testing!) or install proper CA certs

**Issue:** Slack webhook returns 403  
**Solution:** Verify webhook URL is correct and not expired

**Issue:** psutil not returning accurate CPU usage  
**Solution:** Increase interval parameter: `psutil.cpu_percent(interval=2)`

**Issue:** Permission denied reading disk usage  
**Solution:** Run script with appropriate permissions or change disk path

## Learning Resources
- [Requests Documentation](https://requests.readthedocs.io/)
- [psutil Documentation](https://psutil.readthedocs.io/)
- [Slack Webhooks](https://api.slack.com/messaging/webhooks)
- [Python SMTP](https://docs.python.org/3/library/smtplib.html)

---

**Completion Time:** 2-3 hours  
**Difficulty:** Beginner  
**Next Project:** Log Parser and Analyzer

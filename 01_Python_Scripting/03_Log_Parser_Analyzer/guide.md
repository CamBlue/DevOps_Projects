# Log Parser and Analyzer

## Project Overview
**Difficulty:** Beginner-Intermediate  
**Estimated Time:** 3-4 hours  
**Skills Practiced:** Python, Regular Expressions, File I/O, Data Analysis

### What You'll Build
A Python tool that:
- Parses application and system logs from various sources
- Filters logs by severity level (ERROR, WARNING, INFO)
- Extracts patterns using regex (IP addresses, error codes, timestamps)
- Generates summary reports and statistics
- Identifies common errors and anomalies
- Exports results to CSV/JSON

### Why This Matters
Log analysis is critical for debugging, monitoring, and security. This project teaches you to extract meaningful insights from large log files—a skill that mirrors tools like Splunk and ELK stack.

### Prerequisites
- Python 3.8+ installed
- Basic understanding of regular expressions
- Sample log files for testing

---

## Step-by-Step Implementation

### Step 1: Project Setup
```bash
mkdir log-parser
cd log-parser
python3 -m venv venv
source venv/bin/activate
pip install pandas tabulate python-dateutil
```

### Step 2: Create Project Structure
```
log-parser/
├── log_parser.py
├── patterns.py
├── analysis.py
├── exporters.py
├── sample_logs/
│   ├── application.log
│   ├── access.log
│   └── error.log
├── requirements.txt
└── README.md
```

### Step 3: Define Log Patterns

Create `patterns.py`:
```python
import re
from enum import Enum

class LogLevel(Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"

# Common log patterns
PATTERNS = {
    'apache_access': r'(\S+) \S+ \S+ \[([^\]]+)\] "(\S+) (\S+) \S+" (\d+) (\d+)',
    'timestamp': r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}',
    'ip_address': r'\b(?:\d{1,3}\\.){3}\d{1,3}\b',
    'error_code': r'(?:error|exception)\s+\d+',
    'http_status': r'\s(\d{3})\s',
    'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    'url': r'https?://[^\s]+',
}

def extract_log_level(line):
    for level in LogLevel:
        if level.value in line.upper():
            return level.value
    return "UNKNOWN"

def extract_timestamp(line):
    match = re.search(PATTERNS['timestamp'], line)
    return match.group(0) if match else None

def extract_ip_addresses(line):
    return re.findall(PATTERNS['ip_address'], line)
```

### Step 4: Implement Log Parser

Create `log_parser.py`:
```python
import re
from datetime import datetime
from patterns import extract_log_level, extract_timestamp, extract_ip_addresses

class LogParser:
    def __init__(self, log_file):
        self.log_file = log_file
        self.entries = []

    def parse(self):
        with open(self.log_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                entry = self.parse_line(line, line_num)
                if entry:
                    self.entries.append(entry)
        return self.entries

    def parse_line(self, line, line_num):
        return {
            'line_number': line_num,
            'raw': line.strip(),
            'level': extract_log_level(line),
            'timestamp': extract_timestamp(line),
            'ip_addresses': extract_ip_addresses(line)
        }

    def filter_by_level(self, level):
        return [e for e in self.entries if e['level'] == level]

    def filter_by_time_range(self, start, end):
        filtered = []
        for entry in self.entries:
            if entry['timestamp']:
                ts = datetime.fromisoformat(entry['timestamp'])
                if start <= ts <= end:
                    filtered.append(entry)
        return filtered

    def search_pattern(self, pattern):
        regex = re.compile(pattern, re.IGNORECASE)
        return [e for e in self.entries if regex.search(e['raw'])]
```

### Step 5: Implement Analysis Functions

Create `analysis.py`:
```python
from collections import Counter
import pandas as pd

class LogAnalyzer:
    def __init__(self, entries):
        self.entries = entries

    def count_by_level(self):
        levels = [e['level'] for e in self.entries]
        return dict(Counter(levels))

    def top_errors(self, n=10):
        errors = [e['raw'] for e in self.entries if e['level'] == 'ERROR']
        return Counter(errors).most_common(n)

    def top_ip_addresses(self, n=10):
        all_ips = []
        for entry in self.entries:
            all_ips.extend(entry.get('ip_addresses', []))
        return Counter(all_ips).most_common(n)

    def error_rate_over_time(self, interval='1H'):
        df = pd.DataFrame(self.entries)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')

        error_df = df[df['level'] == 'ERROR']
        return error_df.resample(interval).size()

    def generate_summary(self):
        return {
            'total_entries': len(self.entries),
            'level_distribution': self.count_by_level(),
            'top_errors': self.top_errors(5),
            'top_ips': self.top_ip_addresses(5)
        }
```

### Step 6: Add Export Functionality

Create `exporters.py`:
```python
import json
import csv
from datetime import datetime

def export_to_json(data, filename=None):
    if not filename:
        filename = f"log_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    print(f"✓ Exported to {filename}")

def export_to_csv(entries, filename=None):
    if not filename:
        filename = f"log_entries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    if not entries:
        return

    keys = entries[0].keys()
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(entries)
    print(f"✓ Exported to {filename}")

def export_to_html(summary, filename=None):
    if not filename:
        filename = f"log_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

    html = f'''
    <html>
    <head><title>Log Analysis Report</title></head>
    <body>
        <h1>Log Analysis Report</h1>
        <p>Generated: {datetime.now()}</p>
        <h2>Summary</h2>
        <p>Total Entries: {summary['total_entries']}</p>
        <h3>Level Distribution</h3>
        <table border="1">
            <tr><th>Level</th><th>Count</th></tr>
    '''

    for level, count in summary['level_distribution'].items():
        html += f"<tr><td>{level}</td><td>{count}</td></tr>"

    html += '''
        </table>
    </body>
    </html>
    '''

    with open(filename, 'w') as f:
        f.write(html)
    print(f"✓ Exported report to {filename}")
```

### Step 7: Create Main CLI

Add to `log_parser.py`:
```python
import argparse
from tabulate import tabulate

def main():
    parser = argparse.ArgumentParser(description='Parse and analyze log files')
    parser.add_argument('logfile', help='Path to log file')
    parser.add_argument('--level', help='Filter by log level')
    parser.add_argument('--search', help='Search for pattern')
    parser.add_argument('--export-json', action='store_true')
    parser.add_argument('--export-csv', action='store_true')
    parser.add_argument('--report', action='store_true')

    args = parser.parse_args()

    # Parse logs
    print(f"📖 Parsing {args.logfile}...")
    parser_obj = LogParser(args.logfile)
    entries = parser_obj.parse()
    print(f"✓ Parsed {len(entries)} log entries\n")

    # Apply filters
    if args.level:
        entries = parser_obj.filter_by_level(args.level)
        print(f"Filtered to {len(entries)} {args.level} entries")

    if args.search:
        entries = parser_obj.search_pattern(args.search)
        print(f"Found {len(entries)} matches for '{args.search}'")

    # Analysis
    analyzer = LogAnalyzer(entries)
    summary = analyzer.generate_summary()

    # Display summary
    print("\n📊 Analysis Summary:")
    print(f"Total Entries: {summary['total_entries']}")
    print("\nLevel Distribution:")
    print(tabulate(summary['level_distribution'].items(), headers=['Level', 'Count']))

    # Exports
    if args.export_json:
        export_to_json(entries)
    if args.export_csv:
        export_to_csv(entries)
    if args.report:
        export_to_html(summary)

if __name__ == "__main__":
    main()
```

### Step 8: Create Sample Log Files

Create `sample_logs/application.log`:
```
2024-03-09 10:15:23 INFO User 192.168.1.100 logged in successfully
2024-03-09 10:15:45 WARNING Database connection slow: 2.3s
2024-03-09 10:16:12 ERROR Failed to process payment: transaction_id=12345
2024-03-09 10:16:15 ERROR Database connection failed: timeout after 30s
2024-03-09 10:17:00 INFO User 192.168.1.101 logged out
2024-03-09 10:17:23 ERROR Failed to process payment: transaction_id=12346
2024-03-09 10:18:45 WARNING High memory usage: 85%
2024-03-09 10:19:12 ERROR Failed to send email to user@example.com
```

### Step 9: Test Your Implementation

```bash
# Basic parsing
python log_parser.py sample_logs/application.log

# Filter by level
python log_parser.py sample_logs/application.log --level ERROR

# Search for pattern
python log_parser.py sample_logs/application.log --search "payment"

# Generate reports
python log_parser.py sample_logs/application.log --report --export-json --export-csv
```

### Step 10: Add Real-World Features

**Tail mode for live logs:**
```python
import time

def tail_file(filename, callback):
    with open(filename, 'r') as f:
        f.seek(0, 2)  # Go to end of file
        while True:
            line = f.readline()
            if line:
                callback(line)
            else:
                time.sleep(0.1)
```

---

## Success Criteria
- [ ] Successfully parses logs and extracts structured data
- [ ] Regex patterns correctly identify IPs, timestamps, errors
- [ ] Can filter logs by level and time range
- [ ] Generates summary statistics and reports
- [ ] Exports data to JSON, CSV, and HTML formats
- [ ] Handles large log files efficiently

## Extension Ideas
1. **Live Monitoring:** Tail log files and alert on errors in real-time
2. **Multi-File Support:** Parse multiple log files and aggregate results
3. **Geo-IP Lookup:** Map IP addresses to geographic locations
4. **Anomaly Detection:** Use statistics to detect unusual patterns
5. **Web Dashboard:** Flask app to visualize log analysis
6. **Elasticsearch Integration:** Send parsed logs to Elasticsearch
7. **Custom Patterns:** Allow users to define custom regex patterns

---

**Completion Time:** 3-4 hours  
**Difficulty:** Beginner-Intermediate  
**Next Project:** SSL Certificate Monitor

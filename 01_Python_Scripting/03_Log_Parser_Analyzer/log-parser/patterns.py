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
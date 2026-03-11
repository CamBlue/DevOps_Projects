import argparse
from tabulate import tabulate
import re
from datetime import datetime
from patterns import extract_log_level, extract_timestamp, extract_ip_addresses
from analysis import LogAnalyzer
from exporters import export_to_json



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
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
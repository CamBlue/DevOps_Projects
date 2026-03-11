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
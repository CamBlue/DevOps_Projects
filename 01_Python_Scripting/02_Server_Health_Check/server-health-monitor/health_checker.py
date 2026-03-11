import requests
import socket
import psutil
import yaml
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




def main():
    print("🏥 Starting Health Check Monitor...\n")

    # Load configuration
    config = load_config('servers.yaml')
    

    # Run health checks
    results = run_health_checks(config)

    # Display results
    print("\n📊 Health Check Results:")
    print("-" * 60)
    for result in results:
        status_emoji = "✓" if result['status'] == "HEALTHY" else "✗"
        print(f"{status_emoji} {result['server_name']}: {result['status']}")

    # Process alerts
    #process_alerts(results, config)

    # Generate report
    generate_html_report(results)

    print("\n✓ Health check complete!")

if __name__ == "__main__":
    main()
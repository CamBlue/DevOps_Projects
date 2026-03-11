import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


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
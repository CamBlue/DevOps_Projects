import click
from datetime import datetime, timedelta, timezone
from rich.table import Table
from helpers import get_client, console
from botocore.exceptions import ClientError


@click.group()
@click.pass_context
def metrics(ctx):
    """Query CloudWatch metrics"""
    pass


@metrics.command('get')
@click.argument('namespace')
@click.argument('metric_name')
@click.option('--dimension-name', default=None, help='Dimension name (e.g. InstanceId)')
@click.option('--dimension-value', default=None, help='Dimension value (e.g. i-0abc123)')
@click.option('--stat', type=click.Choice(['Average', 'Sum', 'Minimum', 'Maximum', 'SampleCount']),
              default='Average', help='Statistic to retrieve')
@click.option('--period', default=300, type=int, help='Period in seconds (default 300 = 5 min)')
@click.option('--hours', default=1, type=int, help='How many hours back to query (default 1)')
@click.pass_context
def get_metric(ctx, namespace, metric_name, dimension_name, dimension_value, stat, period, hours):
    """Get metric statistics from CloudWatch

    \b
    Common examples:
      devops-cli metrics get AWS/EC2 CPUUtilization --dimension-name InstanceId --dimension-value i-0abc123
      devops-cli metrics get AWS/EKS cluster_failed_node_count --dimension-name ClusterName --dimension-value my-cluster
      devops-cli metrics get AWS/Lambda Invocations --dimension-name FunctionName --dimension-value my-func --stat Sum
    """
    client = get_client('cloudwatch', ctx.obj.get('region'))

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=hours)

    kwargs = {
        'Namespace': namespace,
        'MetricName': metric_name,
        'StartTime': start_time,
        'EndTime': end_time,
        'Period': period,
        'Statistics': [stat],
    }

    if dimension_name and dimension_value:
        kwargs['Dimensions'] = [{'Name': dimension_name, 'Value': dimension_value}]

    try:
        response = client.get_metric_statistics(**kwargs)
    except ClientError as e:
        console.print(f"[red]AWS error: {e}[/red]")
        return

    datapoints = sorted(response.get('Datapoints', []), key=lambda d: d['Timestamp'])

    if not datapoints:
        console.print("[yellow]No datapoints found for the given time range.[/yellow]")
        return

    table = Table(title=f"{namespace} / {metric_name} ({stat})")
    table.add_column("Timestamp", style="dim")
    table.add_column(stat, justify="right", style="green")
    table.add_column("Unit")

    for dp in datapoints:
        ts = dp['Timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        value = f"{dp[stat]:.2f}"
        unit = dp.get('Unit', 'N/A')
        table.add_row(ts, value, unit)

    console.print(table)

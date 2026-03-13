import click
import json
import yaml
from datetime import datetime, timedelta, timezone
from rich.table import Table
from rich.panel import Panel
from helpers import get_client, console
from botocore.exceptions import ClientError


@click.group('lambda-func')
@click.pass_context
def lambda_func(ctx):
    """Manage AWS Lambda functions"""
    pass


@lambda_func.command('list')
@click.option('--format', 'fmt',
              type=click.Choice(['table', 'json', 'yaml']),
              default='table', help='Output format')
@click.pass_context
def list_functions(ctx, fmt):
    """List Lambda functions"""
    client = get_client('lambda', ctx.obj.get('region'))

    try:
        response = client.list_functions()
    except ClientError as e:
        console.print(f"[red]AWS error: {e}[/red]")
        return

    functions = response.get('Functions', [])

    if not functions:
        console.print("[yellow]No Lambda functions found.[/yellow]")
        return

    if fmt == 'table':
        table = Table(title="Lambda Functions")
        table.add_column("Function Name", style="cyan")
        table.add_column("Runtime")
        table.add_column("Memory (MB)", justify="right")
        table.add_column("Timeout (s)", justify="right")
        table.add_column("Code Size (KB)", justify="right")
        table.add_column("Last Modified")

        for fn in functions:
            code_kb = f"{fn.get('CodeSize', 0) / 1024:.0f}"
            table.add_row(
                fn['FunctionName'],
                fn.get('Runtime', 'N/A'),
                str(fn.get('MemorySize', 'N/A')),
                str(fn.get('Timeout', 'N/A')),
                code_kb,
                fn.get('LastModified', 'N/A')[:19],
            )
        console.print(table)

    elif fmt == 'json':
        console.print(json.dumps(functions, indent=2, default=str))

    elif fmt == 'yaml':
        console.print(yaml.dump(functions, default_flow_style=False))


@lambda_func.command('describe')
@click.argument('function_name')
@click.pass_context
def describe_function(ctx, function_name):
    """Show detailed info for a Lambda function"""
    client = get_client('lambda', ctx.obj.get('region'))

    try:
        fn = client.get_function(FunctionName=function_name)
    except ClientError as e:
        console.print(f"[red]Could not describe function '{function_name}': {e}[/red]")
        return

    config = fn['Configuration']

    console.print(Panel(f"[bold cyan]{config['FunctionName']}[/bold cyan]", title="Lambda Function"))
    console.print(f"  ARN:          {config.get('FunctionArn', 'N/A')}")
    console.print(f"  Runtime:      {config.get('Runtime', 'N/A')}")
    console.print(f"  Handler:      {config.get('Handler', 'N/A')}")
    console.print(f"  Memory:       {config.get('MemorySize', 'N/A')} MB")
    console.print(f"  Timeout:      {config.get('Timeout', 'N/A')} seconds")
    console.print(f"  Code Size:    {config.get('CodeSize', 0) / 1024:.0f} KB")
    console.print(f"  Last Modified:{config.get('LastModified', 'N/A')}")
    console.print(f"  Description:  {config.get('Description', 'N/A')}")
    console.print(f"  Role:         {config.get('Role', 'N/A')}")

    # VPC config
    vpc = config.get('VpcConfig', {})
    if vpc.get('VpcId'):
        console.print(f"\n[bold]VPC:[/bold]")
        console.print(f"  VPC ID:       {vpc.get('VpcId')}")
        console.print(f"  Subnets:      {', '.join(vpc.get('SubnetIds', []))}")
        console.print(f"  Sec Groups:   {', '.join(vpc.get('SecurityGroupIds', []))}")

    # Layers
    layers = config.get('Layers', [])
    if layers:
        console.print(f"\n[bold]Layers:[/bold]")
        for layer in layers:
            console.print(f"  {layer.get('Arn', 'N/A')}")

    # Environment variables (names only, not values — for security)
    env_vars = config.get('Environment', {}).get('Variables', {})
    if env_vars:
        console.print(f"\n[bold]Environment Variables:[/bold]")
        for key in env_vars:
            console.print(f"  {key}: [dim]****[/dim]")


@lambda_func.command('invoke')
@click.argument('function_name')
@click.option('--payload', default='{}', help='JSON payload to send (default: {})')
@click.pass_context
def invoke_function(ctx, function_name, payload):
    """Invoke a Lambda function"""
    client = get_client('lambda', ctx.obj.get('region'))

    # Validate the payload is valid JSON
    try:
        json.loads(payload)
    except json.JSONDecodeError:
        console.print("[red]Invalid JSON payload.[/red]")
        return

    console.print(f"[bold]Invoking [cyan]{function_name}[/cyan]...[/bold]")

    try:
        response = client.invoke(
            FunctionName=function_name,
            Payload=payload.encode('utf-8'),
        )
    except ClientError as e:
        console.print(f"[red]Failed to invoke: {e}[/red]")
        return

    status_code = response.get('StatusCode', 'N/A')
    func_error = response.get('FunctionError', None)

    # Read the response payload
    response_payload = response['Payload'].read().decode('utf-8')

    if func_error:
        console.print(f"[red]Function returned error ({func_error}):[/red]")
        try:
            console.print(json.dumps(json.loads(response_payload), indent=2))
        except json.JSONDecodeError:
            console.print(response_payload)
    else:
        console.print(f"[green]Status: {status_code}[/green]")
        try:
            console.print(json.dumps(json.loads(response_payload), indent=2))
        except json.JSONDecodeError:
            console.print(response_payload)


@lambda_func.command('errors')
@click.argument('function_name')
@click.option('--hours', default=24, type=int, help='How many hours back to check (default 24)')
@click.pass_context
def function_errors(ctx, function_name, hours):
    """Check recent errors for a Lambda function"""
    cw = get_client('cloudwatch', ctx.obj.get('region'))

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=hours)

    # Get error count
    try:
        errors_resp = cw.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName='Errors',
            Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Sum'],
        )
        invocations_resp = cw.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName='Invocations',
            Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Sum'],
        )
        duration_resp = cw.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName='Duration',
            Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Average', 'Maximum'],
        )
    except ClientError as e:
        console.print(f"[red]AWS error: {e}[/red]")
        return

    error_points = sorted(errors_resp.get('Datapoints', []), key=lambda d: d['Timestamp'])
    invoc_points = sorted(invocations_resp.get('Datapoints', []), key=lambda d: d['Timestamp'])
    dur_points = sorted(duration_resp.get('Datapoints', []), key=lambda d: d['Timestamp'])

    total_errors = sum(dp['Sum'] for dp in error_points)
    total_invocations = sum(dp['Sum'] for dp in invoc_points)
    error_rate = (total_errors / total_invocations * 100) if total_invocations > 0 else 0

    console.print(Panel(
        f"[bold cyan]{function_name}[/bold cyan] — last {hours} hours",
        title="Lambda Health"
    ))

    # Color based on error rate
    if error_rate > 5:
        rate_color = "red"
    elif error_rate > 1:
        rate_color = "yellow"
    else:
        rate_color = "green"

    console.print(f"  Total Invocations: [bold]{int(total_invocations)}[/bold]")
    console.print(f"  Total Errors:      [bold red]{int(total_errors)}[/bold red]")
    console.print(f"  Error Rate:        [{rate_color}]{error_rate:.1f}%[/{rate_color}]")

    if dur_points:
        avg_dur = sum(dp['Average'] for dp in dur_points) / len(dur_points)
        max_dur = max(dp['Maximum'] for dp in dur_points)
        console.print(f"  Avg Duration:      {avg_dur:.0f} ms")
        console.print(f"  Max Duration:      {max_dur:.0f} ms")

    if error_points:
        console.print(f"\n[bold]Errors by hour:[/bold]")
        table = Table()
        table.add_column("Time", style="dim")
        table.add_column("Errors", justify="right")

        for dp in error_points:
            err_count = int(dp['Sum'])
            if err_count > 0:
                table.add_row(
                    dp['Timestamp'].strftime('%Y-%m-%d %H:%M'),
                    f"[red]{err_count}[/red]",
                )
        console.print(table)

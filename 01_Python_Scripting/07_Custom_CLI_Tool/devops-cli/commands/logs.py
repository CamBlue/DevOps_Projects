import click
import json
import yaml
from datetime import datetime, timedelta, timezone
from rich.table import Table
from helpers import get_client, console
from botocore.exceptions import ClientError


@click.group()
@click.pass_context
def logs(ctx):
    """View and search CloudWatch log groups and events"""
    pass


@logs.command('list')
@click.option('--prefix', default=None, help='Filter log groups by name prefix')
@click.option('--format', 'fmt',
              type=click.Choice(['table', 'json', 'yaml']),
              default='table', help='Output format')
@click.pass_context
def list_log_groups(ctx, prefix, fmt):
    """List CloudWatch log groups"""
    client = get_client('logs', ctx.obj.get('region'))

    kwargs = {}
    if prefix:
        kwargs['logGroupNamePrefix'] = prefix

    try:
        response = client.describe_log_groups(**kwargs)
    except ClientError as e:
        console.print(f"[red]AWS error: {e}[/red]")
        return

    groups = response.get('logGroups', [])

    if not groups:
        console.print("[yellow]No log groups found.[/yellow]")
        return

    if fmt == 'table':
        table = Table(title="CloudWatch Log Groups")
        table.add_column("Log Group Name", style="cyan")
        table.add_column("Stored Bytes", justify="right")
        table.add_column("Retention (days)", justify="center")
        table.add_column("Created")

        for g in groups:
            stored = g.get('storedBytes', 0)
            if stored >= 1_073_741_824:
                size_str = f"{stored / 1_073_741_824:.1f} GB"
            elif stored >= 1_048_576:
                size_str = f"{stored / 1_048_576:.1f} MB"
            elif stored >= 1024:
                size_str = f"{stored / 1024:.1f} KB"
            else:
                size_str = f"{stored} B"

            retention = str(g.get('retentionInDays', 'Never expires'))
            created_ts = g.get('creationTime', 0) / 1000
            created = datetime.fromtimestamp(created_ts, tz=timezone.utc).strftime('%Y-%m-%d') if created_ts else 'N/A'

            table.add_row(
                g['logGroupName'],
                size_str,
                retention,
                created,
            )
        console.print(table)

    elif fmt == 'json':
        console.print(json.dumps(groups, indent=2, default=str))

    elif fmt == 'yaml':
        console.print(yaml.dump(groups, default_flow_style=False))


@logs.command('tail')
@click.argument('log_group')
@click.option('--minutes', default=30, type=int, help='How many minutes back to look (default 30)')
@click.option('--filter', 'filter_pattern', default=None, help='CloudWatch filter pattern (e.g. "ERROR")')
@click.option('--limit', 'max_events', default=50, type=int, help='Max events to return (default 50)')
@click.pass_context
def tail_logs(ctx, log_group, minutes, filter_pattern, max_events):
    """Tail recent log events from a log group"""
    client = get_client('logs', ctx.obj.get('region'))

    start_time = int((datetime.now(timezone.utc) - timedelta(minutes=minutes)).timestamp() * 1000)

    kwargs = {
        'logGroupName': log_group,
        'startTime': start_time,
        'limit': max_events,
        'interleaved': True,
    }
    if filter_pattern:
        kwargs['filterPattern'] = filter_pattern

    try:
        response = client.filter_log_events(**kwargs)
    except ClientError as e:
        console.print(f"[red]AWS error: {e}[/red]")
        return

    events = response.get('events', [])

    if not events:
        console.print(f"[yellow]No log events found in the last {minutes} minutes.[/yellow]")
        return

    console.print(f"[bold]Last {len(events)} events from [cyan]{log_group}[/cyan][/bold]\n")

    for event in events:
        ts = datetime.fromtimestamp(event['timestamp'] / 1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        message = event.get('message', '').strip()
        stream = event.get('logStreamName', 'unknown')

        # Color-code common log levels
        if 'ERROR' in message or 'FATAL' in message:
            console.print(f"[dim]{ts}[/dim] [dim]{stream}[/dim]  [red]{message}[/red]")
        elif 'WARN' in message:
            console.print(f"[dim]{ts}[/dim] [dim]{stream}[/dim]  [yellow]{message}[/yellow]")
        else:
            console.print(f"[dim]{ts}[/dim] [dim]{stream}[/dim]  {message}")

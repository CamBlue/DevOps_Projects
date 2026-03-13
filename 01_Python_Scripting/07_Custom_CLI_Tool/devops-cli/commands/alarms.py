import click
import json
import yaml
from rich.table import Table
from helpers import get_client, console
from botocore.exceptions import ClientError


@click.group()
@click.pass_context
def alarms(ctx):
    """View and manage CloudWatch alarms"""
    pass


@alarms.command('list')
@click.option('--state', type=click.Choice(['OK', 'ALARM', 'INSUFFICIENT_DATA', 'all']),
              default='all', help='Filter by alarm state')
@click.option('--format', 'fmt',
              type=click.Choice(['table', 'json', 'yaml']),
              default='table', help='Output format')
@click.pass_context
def list_alarms(ctx, state, fmt):
    """List CloudWatch alarms"""
    client = get_client('cloudwatch', ctx.obj.get('region'))

    kwargs = {}
    if state != 'all':
        kwargs['StateValue'] = state

    try:
        response = client.describe_alarms(**kwargs)
    except ClientError as e:
        console.print(f"[red]AWS error: {e}[/red]")
        return

    alarm_list = response.get('MetricAlarms', [])

    if not alarm_list:
        console.print("[yellow]No alarms found.[/yellow]")
        return

    if fmt == 'table':
        table = Table(title="CloudWatch Alarms")
        table.add_column("Alarm Name", style="cyan")
        table.add_column("State")
        table.add_column("Metric")
        table.add_column("Namespace")
        table.add_column("Threshold")
        table.add_column("Updated")

        for a in alarm_list:
            alarm_state = a.get('StateValue', 'UNKNOWN')
            if alarm_state == 'ALARM':
                state_display = "[red]ALARM[/red]"
            elif alarm_state == 'OK':
                state_display = "[green]OK[/green]"
            else:
                state_display = f"[yellow]{alarm_state}[/yellow]"

            comparison = a.get('ComparisonOperator', '')
            threshold = a.get('Threshold', 'N/A')
            threshold_str = f"{comparison} {threshold}"

            updated = str(a.get('StateUpdatedTimestamp', 'N/A'))[:19]

            table.add_row(
                a.get('AlarmName', 'N/A'),
                state_display,
                a.get('MetricName', 'N/A'),
                a.get('Namespace', 'N/A'),
                threshold_str,
                updated,
            )
        console.print(table)

    elif fmt == 'json':
        console.print(json.dumps(alarm_list, indent=2, default=str))

    elif fmt == 'yaml':
        console.print(yaml.dump(alarm_list, default_flow_style=False))


@alarms.command('status')
@click.pass_context
def alarm_status(ctx):
    """Show summary of alarms currently in ALARM state"""
    client = get_client('cloudwatch', ctx.obj.get('region'))

    try:
        response = client.describe_alarms(StateValue='ALARM')
    except ClientError as e:
        console.print(f"[red]AWS error: {e}[/red]")
        return

    alarm_list = response.get('MetricAlarms', [])

    if not alarm_list:
        console.print("[green]No alarms currently firing.[/green]")
        return

    console.print(f"[bold red]{len(alarm_list)} alarm(s) currently in ALARM state:[/bold red]\n")

    for a in alarm_list:
        console.print(f"  [red]{a.get('AlarmName')}[/red]")
        console.print(f"    Metric:      {a.get('Namespace')}/{a.get('MetricName')}")
        console.print(f"    Threshold:   {a.get('ComparisonOperator')} {a.get('Threshold')}")
        console.print(f"    Description: {a.get('AlarmDescription', 'N/A')}")
        console.print(f"    Since:       {a.get('StateUpdatedTimestamp', 'N/A')}")
        console.print(f"    Reason:      {a.get('StateReason', 'N/A')}")
        console.print()

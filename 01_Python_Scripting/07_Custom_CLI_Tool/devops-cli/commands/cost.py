import click
from datetime import datetime, timedelta, timezone
from rich.table import Table
from helpers import get_client, console
from botocore.exceptions import ClientError


@click.group()
@click.pass_context
def cost(ctx):
    """View AWS cost and usage data"""
    pass


@cost.command('monthly')
@click.option('--months', default=1, type=int, help='How many months back to show (default 1)')
@click.pass_context
def monthly_cost(ctx, months):
    """Show total cost for current/recent months"""
    # Cost Explorer must be called from us-east-1
    client = get_client('ce', 'us-east-1')

    today = datetime.now(timezone.utc).date()
    start_month = today.month - months
    start_year = today.year
    while start_month <= 0:
        start_month += 12
        start_year -= 1

    start_date = f"{start_year}-{start_month:02d}-01"
    end_date = f"{today.year}-{today.month:02d}-{today.day:02d}"

    try:
        response = client.get_cost_and_usage(
            TimePeriod={'Start': start_date, 'End': end_date},
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
        )
    except ClientError as e:
        console.print(f"[red]AWS error: {e}[/red]")
        return

    results = response.get('ResultsByTime', [])

    if not results:
        console.print("[yellow]No cost data found.[/yellow]")
        return

    table = Table(title="AWS Monthly Costs")
    table.add_column("Period", style="cyan")
    table.add_column("Cost (USD)", justify="right", style="green")

    total = 0.0
    for period in results:
        start = period['TimePeriod']['Start']
        end = period['TimePeriod']['End']
        amount = float(period['Total']['UnblendedCost']['Amount'])
        total += amount
        table.add_row(f"{start} → {end}", f"${amount:,.2f}")

    table.add_row("[bold]Total[/bold]", f"[bold]${total:,.2f}[/bold]")
    console.print(table)


@cost.command('by-service')
@click.option('--days', default=30, type=int, help='How many days back to analyze (default 30)')
@click.option('--top', default=10, type=int, help='Show top N services (default 10)')
@click.pass_context
def cost_by_service(ctx, days, top):
    """Show cost breakdown by AWS service"""
    client = get_client('ce', 'us-east-1')

    today = datetime.now(timezone.utc).date()
    start_date = (today - timedelta(days=days)).isoformat()
    end_date = today.isoformat()

    try:
        response = client.get_cost_and_usage(
            TimePeriod={'Start': start_date, 'End': end_date},
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}],
        )
    except ClientError as e:
        console.print(f"[red]AWS error: {e}[/red]")
        return

    # Aggregate costs across time periods
    service_costs = {}
    for period in response.get('ResultsByTime', []):
        for group in period.get('Groups', []):
            service = group['Keys'][0]
            amount = float(group['Metrics']['UnblendedCost']['Amount'])
            service_costs[service] = service_costs.get(service, 0.0) + amount

    if not service_costs:
        console.print("[yellow]No cost data found.[/yellow]")
        return

    # Sort by cost descending, take top N
    sorted_services = sorted(service_costs.items(), key=lambda x: x[1], reverse=True)[:top]
    total = sum(service_costs.values())

    table = Table(title=f"Top {top} Services by Cost (last {days} days)")
    table.add_column("Service", style="cyan")
    table.add_column("Cost (USD)", justify="right", style="green")
    table.add_column("% of Total", justify="right")

    for service, amount in sorted_services:
        pct = (amount / total * 100) if total > 0 else 0
        table.add_row(service, f"${amount:,.2f}", f"{pct:.1f}%")

    table.add_row("[bold]Total (all services)[/bold]", f"[bold]${total:,.2f}[/bold]", "100%")
    console.print(table)

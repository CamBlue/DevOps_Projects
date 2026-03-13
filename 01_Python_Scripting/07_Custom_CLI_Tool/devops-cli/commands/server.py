import click
import json
import yaml
from rich.table import Table
from helpers import get_client, console
from botocore.exceptions import ClientError


@click.group()
@click.pass_context
def server(ctx):
    """Manage servers (backed by AWS EC2)"""
    pass


@server.command('list')
@click.option('--status', 'state',
              type=click.Choice(['running', 'stopped', 'all']),
              default='all', help='Filter by instance state')
@click.option('--format', 'fmt',
              type=click.Choice(['table', 'json', 'yaml']),
              default='table', help='Output format')
@click.pass_context
def list_servers(ctx, state, fmt):
    """List EC2 instances"""
    ec2 = get_client('ec2', ctx.obj.get('region'))

    filters = []
    if state != 'all':
        filters.append({'Name': 'instance-state-name', 'Values': [state]})

    try:
        response = ec2.describe_instances(Filters=filters)
    except ClientError as e:
        console.print(f"[red]AWS error: {e}[/red]")
        return

    servers = []
    for reservation in response['Reservations']:
        for inst in reservation['Instances']:
            name_tag = next(
                (t['Value'] for t in inst.get('Tags', []) if t['Key'] == 'Name'),
                inst['InstanceId']
            )
            servers.append({
                'name': name_tag,
                'instance_id': inst['InstanceId'],
                'status': inst['State']['Name'],
                'type': inst['InstanceType'],
                'ip': inst.get('PublicIpAddress', 'N/A'),
                'private_ip': inst.get('PrivateIpAddress', 'N/A'),
                'launch_time': str(inst.get('LaunchTime', 'N/A')),
            })

    if not servers:
        console.print("[yellow]No instances found.[/yellow]")
        return

    if fmt == 'table':
        table = Table(title="EC2 Instances")
        table.add_column("Name", style="cyan")
        table.add_column("Instance ID", style="dim")
        table.add_column("Status", style="magenta")
        table.add_column("Type")
        table.add_column("Public IP", style="green")
        table.add_column("Private IP")

        for s in servers:
            status_style = "green" if s['status'] == 'running' else "red"
            table.add_row(
                s['name'],
                s['instance_id'],
                f"[{status_style}]{s['status']}[/{status_style}]",
                s['type'],
                s['ip'],
                s['private_ip'],
            )
        console.print(table)

    elif fmt == 'json':
        console.print(json.dumps(servers, indent=2, default=str))

    elif fmt == 'yaml':
        console.print(yaml.dump(servers, default_flow_style=False))


@server.command()
@click.argument('instance_id')
@click.option('--detailed', is_flag=True, help='Show detailed information')
@click.pass_context
def status(ctx, instance_id, detailed):
    """Check instance status (pass instance ID or Name tag)"""
    ec2 = get_client('ec2', ctx.obj.get('region'))

    if not instance_id.startswith('i-'):
        resp = ec2.describe_instances(
            Filters=[{'Name': 'tag:Name', 'Values': [instance_id]}]
        )
        instances = [i for r in resp['Reservations'] for i in r['Instances']]
        if not instances:
            console.print(f"[red]No instance found with Name tag '{instance_id}'[/red]")
            return
        inst = instances[0]
    else:
        try:
            resp = ec2.describe_instances(InstanceIds=[instance_id])
            inst = resp['Reservations'][0]['Instances'][0]
        except (ClientError, IndexError) as e:
            console.print(f"[red]Could not find instance {instance_id}: {e}[/red]")
            return

    name = next(
        (t['Value'] for t in inst.get('Tags', []) if t['Key'] == 'Name'),
        inst['InstanceId']
    )

    console.print(f"[bold]Instance: {name} ({inst['InstanceId']})[/bold]")
    inst_state = inst['State']['Name']
    color = "green" if inst_state == "running" else "red"
    console.print(f"  State:       [{color}]{inst_state}[/{color}]")
    console.print(f"  Type:        {inst['InstanceType']}")
    console.print(f"  Public IP:   [green]{inst.get('PublicIpAddress', 'N/A')}[/green]")
    console.print(f"  Private IP:  {inst.get('PrivateIpAddress', 'N/A')}")
    console.print(f"  Launch Time: {inst.get('LaunchTime', 'N/A')}")

    if detailed:
        console.print(f"  VPC ID:      {inst.get('VpcId', 'N/A')}")
        console.print(f"  Subnet ID:   {inst.get('SubnetId', 'N/A')}")
        console.print(f"  AZ:          {inst['Placement']['AvailabilityZone']}")
        console.print(f"  AMI ID:      {inst['ImageId']}")
        console.print(f"  Key Pair:    {inst.get('KeyName', 'N/A')}")

        sgs = ', '.join(sg['GroupName'] for sg in inst.get('SecurityGroups', []))
        console.print(f"  Sec Groups:  {sgs or 'N/A'}")

        if inst_state == 'running':
            try:
                status_resp = ec2.describe_instance_status(InstanceIds=[inst['InstanceId']])
                if status_resp['InstanceStatuses']:
                    s = status_resp['InstanceStatuses'][0]
                    console.print(f"  System Check: {s['SystemStatus']['Status']}")
                    console.print(f"  Instance Check: {s['InstanceStatus']['Status']}")
            except ClientError:
                pass


@server.command()
@click.argument('instance_id')
@click.confirmation_option(prompt='Are you sure you want to restart this instance?')
@click.pass_context
def restart(ctx, instance_id):
    """Reboot an EC2 instance"""
    ec2 = get_client('ec2', ctx.obj.get('region'))

    with console.status(f"[bold green]Rebooting {instance_id}..."):
        try:
            ec2.reboot_instances(InstanceIds=[instance_id])
        except ClientError as e:
            console.print(f"[red]Failed to reboot: {e}[/red]")
            return

    console.print(f"[green]Reboot command sent to {instance_id}[/green]")


@server.command('start')
@click.argument('instance_id')
@click.pass_context
def start_instance(ctx, instance_id):
    """Start a stopped EC2 instance"""
    ec2 = get_client('ec2', ctx.obj.get('region'))
    try:
        ec2.start_instances(InstanceIds=[instance_id])
        console.print(f"[green]Starting {instance_id}...[/green]")
    except ClientError as e:
        console.print(f"[red]Failed to start: {e}[/red]")


@server.command('stop')
@click.argument('instance_id')
@click.confirmation_option(prompt='Are you sure you want to stop this instance?')
@click.pass_context
def stop_instance(ctx, instance_id):
    """Stop a running EC2 instance"""
    ec2 = get_client('ec2', ctx.obj.get('region'))
    try:
        ec2.stop_instances(InstanceIds=[instance_id])
        console.print(f"[yellow]Stopping {instance_id}...[/yellow]")
    except ClientError as e:
        console.print(f"[red]Failed to stop: {e}[/red]")


def validate_ip(ctx, param, value):
    """Validate IP address"""
    import re
    if value:
        pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
        if not re.match(pattern, value):
            raise click.BadParameter('Invalid IP address format')
    return value


@server.command('add')
@click.argument('name')
@click.option('--ip', callback=validate_ip, required=True, help='Server IP address')
@click.option('--type', type=click.Choice(['web', 'db', 'cache']), required=True)
def add_server(name, ip, type):
    """Add a new server to inventory"""
    console.print(f"Added server {name} ({ip}) as {type}")

import click
import json
import yaml
from rich.table import Table
from helpers import get_client, console
from botocore.exceptions import ClientError


@click.group()
@click.pass_context
def iam(ctx):
    """View IAM users, roles, and their policies"""
    pass


@iam.command('list-users')
@click.option('--format', 'fmt',
              type=click.Choice(['table', 'json', 'yaml']),
              default='table', help='Output format')
@click.pass_context
def list_users(ctx, fmt):
    """List IAM users"""
    client = get_client('iam', ctx.obj.get('region'))

    try:
        paginator = client.get_paginator('list_users')
        users = []
        for page in paginator.paginate():
            users.extend(page['Users'])
    except ClientError as e:
        console.print(f"[red]AWS error: {e}[/red]")
        return

    if not users:
        console.print("[yellow]No IAM users found.[/yellow]")
        return

    if fmt == 'table':
        table = Table(title="IAM Users")
        table.add_column("Username", style="cyan")
        table.add_column("User ID", style="dim")
        table.add_column("ARN")
        table.add_column("Created")
        table.add_column("Password Last Used")

        for u in users:
            pwd_used = str(u.get('PasswordLastUsed', 'Never'))[:19]
            table.add_row(
                u['UserName'],
                u['UserId'],
                u['Arn'],
                str(u['CreateDate'])[:19],
                pwd_used,
            )
        console.print(table)

    elif fmt == 'json':
        console.print(json.dumps(users, indent=2, default=str))

    elif fmt == 'yaml':
        console.print(yaml.dump(users, default_flow_style=False))


@iam.command('list-roles')
@click.option('--prefix', default=None, help='Filter roles by path prefix (e.g. /service-role/)')
@click.option('--format', 'fmt',
              type=click.Choice(['table', 'json', 'yaml']),
              default='table', help='Output format')
@click.pass_context
def list_roles(ctx, prefix, fmt):
    """List IAM roles"""
    client = get_client('iam', ctx.obj.get('region'))

    kwargs = {}
    if prefix:
        kwargs['PathPrefix'] = prefix

    try:
        paginator = client.get_paginator('list_roles')
        roles = []
        for page in paginator.paginate(**kwargs):
            roles.extend(page['Roles'])
    except ClientError as e:
        console.print(f"[red]AWS error: {e}[/red]")
        return

    if not roles:
        console.print("[yellow]No IAM roles found.[/yellow]")
        return

    if fmt == 'table':
        table = Table(title="IAM Roles")
        table.add_column("Role Name", style="cyan")
        table.add_column("Role ID", style="dim")
        table.add_column("Created")
        table.add_column("Description", max_width=40)

        for r in roles:
            table.add_row(
                r['RoleName'],
                r['RoleId'],
                str(r['CreateDate'])[:19],
                r.get('Description', '')[:40],
            )
        console.print(table)

    elif fmt == 'json':
        console.print(json.dumps(roles, indent=2, default=str))

    elif fmt == 'yaml':
        console.print(yaml.dump(roles, default_flow_style=False))


@iam.command('user-policies')
@click.argument('username')
@click.pass_context
def user_policies(ctx, username):
    """Show all policies attached to an IAM user"""
    client = get_client('iam', ctx.obj.get('region'))

    console.print(f"[bold]Policies for user: [cyan]{username}[/cyan][/bold]\n")

    # Managed (attached) policies
    try:
        resp = client.list_attached_user_policies(UserName=username)
        attached = resp.get('AttachedPolicies', [])
    except ClientError as e:
        console.print(f"[red]AWS error: {e}[/red]")
        return

    if attached:
        console.print("[bold]Managed Policies:[/bold]")
        for p in attached:
            console.print(f"  [green]{p['PolicyName']}[/green]")
            console.print(f"    ARN: [dim]{p['PolicyArn']}[/dim]")
    else:
        console.print("[dim]No managed policies attached.[/dim]")

    # Inline policies
    try:
        resp = client.list_user_policies(UserName=username)
        inline = resp.get('PolicyNames', [])
    except ClientError as e:
        console.print(f"[red]AWS error fetching inline policies: {e}[/red]")
        return

    console.print()
    if inline:
        console.print("[bold]Inline Policies:[/bold]")
        for name in inline:
            console.print(f"  [yellow]{name}[/yellow]")
    else:
        console.print("[dim]No inline policies.[/dim]")

    # Groups the user belongs to
    try:
        resp = client.list_groups_for_user(UserName=username)
        groups = resp.get('Groups', [])
    except ClientError as e:
        console.print(f"[red]AWS error fetching groups: {e}[/red]")
        return

    console.print()
    if groups:
        console.print("[bold]Group Memberships:[/bold]")
        for g in groups:
            console.print(f"  {g['GroupName']}")
    else:
        console.print("[dim]Not a member of any groups.[/dim]")


@iam.command('role-policies')
@click.argument('role_name')
@click.pass_context
def role_policies(ctx, role_name):
    """Show all policies attached to an IAM role"""
    client = get_client('iam', ctx.obj.get('region'))

    console.print(f"[bold]Policies for role: [cyan]{role_name}[/cyan][/bold]\n")

    # Managed (attached) policies
    try:
        resp = client.list_attached_role_policies(RoleName=role_name)
        attached = resp.get('AttachedPolicies', [])
    except ClientError as e:
        console.print(f"[red]AWS error: {e}[/red]")
        return

    if attached:
        console.print("[bold]Managed Policies:[/bold]")
        for p in attached:
            console.print(f"  [green]{p['PolicyName']}[/green]")
            console.print(f"    ARN: [dim]{p['PolicyArn']}[/dim]")
    else:
        console.print("[dim]No managed policies attached.[/dim]")

    # Inline policies
    try:
        resp = client.list_role_policies(RoleName=role_name)
        inline = resp.get('PolicyNames', [])
    except ClientError as e:
        console.print(f"[red]AWS error fetching inline policies: {e}[/red]")
        return

    console.print()
    if inline:
        console.print("[bold]Inline Policies:[/bold]")
        for name in inline:
            console.print(f"  [yellow]{name}[/yellow]")
    else:
        console.print("[dim]No inline policies.[/dim]")

import click
import time
from helpers import console


@click.group()
def deploy():
    """Manage deployments"""
    pass


@deploy.command('app')
@click.argument('app_name')
@click.option('--version', default='latest', help='App version to deploy')
@click.option('--environment', type=click.Choice(['dev', 'staging', 'prod']),
              required=True, help='Target environment')
@click.option('--replicas', default=3, type=int, help='Number of replicas')
def deploy_app(app_name, version, environment, replicas):
    """Deploy an application"""
    console.print(f"[bold]Deploying {app_name} v{version} to {environment}[/bold]")

    steps = [
        "Pulling Docker image",
        "Updating configuration",
        "Rolling out deployment",
        "Verifying health checks",
        "Deployment complete"
    ]

    from rich.progress import Progress

    with Progress() as progress:
        task = progress.add_task("[cyan]Deploying...", total=len(steps))

        for step in steps:
            console.print(f"  → {step}")
            time.sleep(1)
            progress.update(task, advance=1)

    console.print(f"[green]{app_name} v{version} deployed successfully[/green]")
    console.print(f"  Replicas: {replicas}")
    console.print(f"  Environment: {environment}")


@deploy.command('rollback')
@click.argument('app_name')
@click.option('--revision', type=int, help='Revision number to rollback to')
@click.confirmation_option(prompt='Are you sure you want to rollback?')
def rollback(app_name, revision):
    """Rollback an application deployment"""
    rev = revision if revision else 'previous'
    console.print(f"[yellow]Rolling back {app_name} to revision {rev}[/yellow]")

    with console.status("[bold yellow]Performing rollback..."):
        time.sleep(2)

    console.print("[green]Rollback completed[/green]")

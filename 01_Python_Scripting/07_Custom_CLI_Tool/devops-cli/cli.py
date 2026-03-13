import click
from commands.server import server
from commands.eks import eks
from commands.logs import logs
from commands.alarms import alarms
from commands.metrics import metrics
from commands.iam import iam
from commands.ecr import ecr
from commands.lambda_func import lambda_func
from commands.cost import cost
from commands.deploy import deploy
from commands.config import config
from helpers import console


@click.group()
@click.version_option(version='1.0.0')
@click.option('--region', default=None, help='AWS region override (e.g. us-west-2)')
@click.pass_context
def cli(ctx, region):
    """
    DevOps CLI - Manage servers and deployments

    A comprehensive tool for DevOps operations.
    """
    ctx.ensure_object(dict)
    ctx.obj['region'] = region


@cli.command()
def info():
    """Show CLI information"""
    console.print("[bold green]DevOps CLI v1.0.0[/bold green]")
    console.print("A powerful tool for DevOps operations")


# Register all command groups
cli.add_command(server)
cli.add_command(eks)
cli.add_command(logs)
cli.add_command(alarms)
cli.add_command(metrics)
cli.add_command(iam)
cli.add_command(ecr)
cli.add_command(lambda_func)
cli.add_command(cost)
cli.add_command(deploy)
cli.add_command(config)


if __name__ == '__main__':
    cli()
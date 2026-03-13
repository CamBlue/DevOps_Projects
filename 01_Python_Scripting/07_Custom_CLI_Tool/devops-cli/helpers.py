import boto3
from rich.console import Console
from botocore.exceptions import ClientError, NoCredentialsError, BotoCoreError

console = Console()


def get_client(service, region=None):
    """Get a boto3 client for any AWS service."""
    try:
        return boto3.client(service, region_name=region)
    except NoCredentialsError:
        console.print("[red]AWS credentials not found. Run 'aws configure' first.[/red]")
        raise SystemExit(1)
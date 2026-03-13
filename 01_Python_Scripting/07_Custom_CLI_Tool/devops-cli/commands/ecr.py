import click
import json
import yaml
from datetime import datetime
from rich.table import Table
from helpers import get_client, console
from botocore.exceptions import ClientError


@click.group()
@click.pass_context
def ecr(ctx):
    """Manage ECR container image repositories"""
    pass


@ecr.command('list')
@click.option('--format', 'fmt',
              type=click.Choice(['table', 'json', 'yaml']),
              default='table', help='Output format')
@click.pass_context
def list_repos(ctx, fmt):
    """List ECR repositories"""
    client = get_client('ecr', ctx.obj.get('region'))

    try:
        response = client.describe_repositories()
    except ClientError as e:
        console.print(f"[red]AWS error: {e}[/red]")
        return

    repos = response.get('repositories', [])

    if not repos:
        console.print("[yellow]No ECR repositories found.[/yellow]")
        return

    if fmt == 'table':
        table = Table(title="ECR Repositories")
        table.add_column("Repository Name", style="cyan")
        table.add_column("URI")
        table.add_column("Tag Mutability")
        table.add_column("Scan on Push")
        table.add_column("Created")

        for r in repos:
            scan = "Yes" if r.get('imageScanningConfiguration', {}).get('scanOnPush') else "No"
            table.add_row(
                r['repositoryName'],
                r.get('repositoryUri', 'N/A'),
                r.get('imageTagMutability', 'N/A'),
                scan,
                str(r.get('createdAt', 'N/A'))[:19],
            )
        console.print(table)

    elif fmt == 'json':
        console.print(json.dumps(repos, indent=2, default=str))

    elif fmt == 'yaml':
        console.print(yaml.dump(repos, default_flow_style=False))


@ecr.command('images')
@click.argument('repo_name')
@click.option('--format', 'fmt',
              type=click.Choice(['table', 'json', 'yaml']),
              default='table', help='Output format')
@click.pass_context
def list_images(ctx, repo_name, fmt):
    """List images in an ECR repository"""
    client = get_client('ecr', ctx.obj.get('region'))

    try:
        response = client.describe_images(repositoryName=repo_name)
    except ClientError as e:
        console.print(f"[red]AWS error: {e}[/red]")
        return

    images = response.get('imageDetails', [])

    if not images:
        console.print(f"[yellow]No images found in '{repo_name}'.[/yellow]")
        return

    # Sort by push date, newest first
    images.sort(key=lambda i: i.get('imagePushedAt', datetime.min), reverse=True)

    if fmt == 'table':
        table = Table(title=f"Images — {repo_name}")
        table.add_column("Tags", style="cyan")
        table.add_column("Digest", style="dim", max_width=25)
        table.add_column("Size (MB)", justify="right")
        table.add_column("Pushed")
        table.add_column("Scan Status")

        for img in images:
            tags = ', '.join(img.get('imageTags', ['<untagged>']))
            digest = img.get('imageDigest', 'N/A')[:25]
            size_mb = f"{img.get('imageSizeInBytes', 0) / 1_048_576:.1f}"
            pushed = str(img.get('imagePushedAt', 'N/A'))[:19]

            scan = img.get('imageScanStatus', {})
            scan_status = scan.get('status', 'NOT_SCANNED')
            if scan_status == 'COMPLETE':
                findings = img.get('imageScanFindingsSummary', {}).get('findingSeverityCounts', {})
                critical = findings.get('CRITICAL', 0)
                high = findings.get('HIGH', 0)
                if critical > 0:
                    scan_display = f"[red]{critical} CRITICAL, {high} HIGH[/red]"
                elif high > 0:
                    scan_display = f"[yellow]{high} HIGH[/yellow]"
                else:
                    scan_display = "[green]Clean[/green]"
            else:
                scan_display = scan_status

            table.add_row(tags, digest, size_mb, pushed, scan_display)
        console.print(table)

    elif fmt == 'json':
        console.print(json.dumps(images, indent=2, default=str))

    elif fmt == 'yaml':
        console.print(yaml.dump(images, default_flow_style=False))


@ecr.command('delete-image')
@click.argument('repo_name')
@click.option('--tag', default=None, help='Image tag to delete')
@click.option('--digest', default=None, help='Image digest to delete')
@click.confirmation_option(prompt='Are you sure you want to delete this image?')
@click.pass_context
def delete_image(ctx, repo_name, tag, digest):
    """Delete an image from an ECR repository"""
    if not tag and not digest:
        console.print("[red]You must provide either --tag or --digest[/red]")
        return

    client = get_client('ecr', ctx.obj.get('region'))

    image_id = {}
    if tag:
        image_id['imageTag'] = tag
    if digest:
        image_id['imageDigest'] = digest

    try:
        response = client.batch_delete_image(
            repositoryName=repo_name,
            imageIds=[image_id],
        )
        deleted = response.get('imageIds', [])
        failures = response.get('failures', [])

        if deleted:
            console.print(f"[green]Deleted image from '{repo_name}'[/green]")
            for d in deleted:
                console.print(f"  Tag: {d.get('imageTag', 'N/A')}, Digest: {d.get('imageDigest', 'N/A')[:25]}")
        if failures:
            for f in failures:
                console.print(f"[red]Failed: {f.get('failureReason')}[/red]")
    except ClientError as e:
        console.print(f"[red]Failed to delete image: {e}[/red]")

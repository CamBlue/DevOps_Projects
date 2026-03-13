import click
import json
import yaml
from rich.table import Table
from rich.panel import Panel
from helpers import get_client, console
from botocore.exceptions import ClientError


@click.group()
@click.pass_context
def eks(ctx):
    """Manage AWS EKS clusters and node groups"""
    pass


@eks.command('list')
@click.option('--format', 'fmt',
              type=click.Choice(['table', 'json', 'yaml']),
              default='table', help='Output format')
@click.pass_context
def list_clusters(ctx, fmt):
    """List all EKS clusters"""
    client = get_client('eks', ctx.obj.get('region'))

    try:
        response = client.list_clusters()
    except ClientError as e:
        console.print(f"[red]AWS error: {e}[/red]")
        return

    cluster_names = response.get('clusters', [])

    if not cluster_names:
        console.print("[yellow]No EKS clusters found.[/yellow]")
        return

    clusters = []
    for name in cluster_names:
        try:
            desc = client.describe_cluster(name=name)['cluster']
            clusters.append({
                'name': desc['name'],
                'status': desc['status'],
                'version': desc.get('version', 'N/A'),
                'endpoint': desc.get('endpoint', 'N/A'),
                'platform_version': desc.get('platformVersion', 'N/A'),
                'created': str(desc.get('createdAt', 'N/A')),
            })
        except ClientError as e:
            console.print(f"[yellow]Could not describe cluster {name}: {e}[/yellow]")

    if fmt == 'table':
        table = Table(title="EKS Clusters")
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="magenta")
        table.add_column("K8s Version", style="green")
        table.add_column("Platform Version")
        table.add_column("Created")

        for c in clusters:
            status_style = "green" if c['status'] == 'ACTIVE' else "yellow"
            table.add_row(
                c['name'],
                f"[{status_style}]{c['status']}[/{status_style}]",
                c['version'],
                c['platform_version'],
                c['created'],
            )
        console.print(table)

    elif fmt == 'json':
        console.print(json.dumps(clusters, indent=2, default=str))

    elif fmt == 'yaml':
        console.print(yaml.dump(clusters, default_flow_style=False))


@eks.command('describe')
@click.argument('cluster_name')
@click.pass_context
def describe_cluster(ctx, cluster_name):
    """Show detailed info for an EKS cluster"""
    client = get_client('eks', ctx.obj.get('region'))

    try:
        resp = client.describe_cluster(name=cluster_name)
        c = resp['cluster']
    except ClientError as e:
        console.print(f"[red]Could not describe cluster '{cluster_name}': {e}[/red]")
        return

    status_color = "green" if c['status'] == 'ACTIVE' else "yellow"

    console.print(Panel(f"[bold cyan]{c['name']}[/bold cyan]", title="EKS Cluster"))
    console.print(f"  Status:           [{status_color}]{c['status']}[/{status_color}]")
    console.print(f"  K8s Version:      [green]{c.get('version', 'N/A')}[/green]")
    console.print(f"  Platform Version: {c.get('platformVersion', 'N/A')}")
    console.print(f"  ARN:              {c.get('arn', 'N/A')}")
    console.print(f"  Endpoint:         {c.get('endpoint', 'N/A')}")
    console.print(f"  Role ARN:         {c.get('roleArn', 'N/A')}")
    console.print(f"  Created:          {c.get('createdAt', 'N/A')}")

    vpc = c.get('resourcesVpcConfig', {})
    console.print(f"\n[bold]Networking:[/bold]")
    console.print(f"  VPC ID:           {vpc.get('vpcId', 'N/A')}")
    console.print(f"  Subnets:          {', '.join(vpc.get('subnetIds', []))}")
    console.print(f"  Security Groups:  {', '.join(vpc.get('securityGroupIds', []))}")
    console.print(f"  Cluster SG:       {vpc.get('clusterSecurityGroupId', 'N/A')}")
    console.print(f"  Public Access:    {vpc.get('endpointPublicAccess', 'N/A')}")
    console.print(f"  Private Access:   {vpc.get('endpointPrivateAccess', 'N/A')}")

    k8s_net = c.get('kubernetesNetworkConfig', {})
    if k8s_net:
        console.print(f"  Service CIDR:     {k8s_net.get('serviceIpv4Cidr', 'N/A')}")
        console.print(f"  IP Family:        {k8s_net.get('ipFamily', 'N/A')}")

    logging_cfg = c.get('logging', {}).get('clusterLogging', [])
    if logging_cfg:
        console.print(f"\n[bold]Logging:[/bold]")
        for log_group in logging_cfg:
            enabled = "[green]enabled[/green]" if log_group.get('enabled') else "[red]disabled[/red]"
            types = ', '.join(log_group.get('types', []))
            console.print(f"  {types}: {enabled}")

    tags = c.get('tags', {})
    if tags:
        console.print(f"\n[bold]Tags:[/bold]")
        for key, value in tags.items():
            console.print(f"  {key}: [green]{value}[/green]")


@eks.command('nodegroups')
@click.argument('cluster_name')
@click.option('--format', 'fmt',
              type=click.Choice(['table', 'json', 'yaml']),
              default='table', help='Output format')
@click.pass_context
def list_nodegroups(ctx, cluster_name, fmt):
    """List node groups for a cluster"""
    client = get_client('eks', ctx.obj.get('region'))

    try:
        response = client.list_nodegroups(clusterName=cluster_name)
    except ClientError as e:
        console.print(f"[red]AWS error: {e}[/red]")
        return

    ng_names = response.get('nodegroups', [])

    if not ng_names:
        console.print(f"[yellow]No node groups found for cluster '{cluster_name}'.[/yellow]")
        return

    nodegroups = []
    for ng_name in ng_names:
        try:
            desc = client.describe_nodegroup(
                clusterName=cluster_name,
                nodegroupName=ng_name
            )['nodegroup']
            scaling = desc.get('scalingConfig', {})
            nodegroups.append({
                'name': desc['nodegroupName'],
                'status': desc['status'],
                'instance_types': ', '.join(desc.get('instanceTypes', [])),
                'capacity_type': desc.get('capacityType', 'N/A'),
                'desired': str(scaling.get('desiredSize', 'N/A')),
                'min': str(scaling.get('minSize', 'N/A')),
                'max': str(scaling.get('maxSize', 'N/A')),
            })
        except ClientError as e:
            console.print(f"[yellow]Could not describe node group {ng_name}: {e}[/yellow]")

    if fmt == 'table':
        table = Table(title=f"Node Groups — {cluster_name}")
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="magenta")
        table.add_column("Instance Types")
        table.add_column("Capacity")
        table.add_column("Desired", justify="center")
        table.add_column("Min", justify="center")
        table.add_column("Max", justify="center")

        for ng in nodegroups:
            status_style = "green" if ng['status'] == 'ACTIVE' else "yellow"
            table.add_row(
                ng['name'],
                f"[{status_style}]{ng['status']}[/{status_style}]",
                ng['instance_types'],
                ng['capacity_type'],
                ng['desired'],
                ng['min'],
                ng['max'],
            )
        console.print(table)

    elif fmt == 'json':
        console.print(json.dumps(nodegroups, indent=2, default=str))

    elif fmt == 'yaml':
        console.print(yaml.dump(nodegroups, default_flow_style=False))


@eks.command('describe-nodegroup')
@click.argument('cluster_name')
@click.argument('nodegroup_name')
@click.pass_context
def describe_nodegroup(ctx, cluster_name, nodegroup_name):
    """Show detailed info for a node group"""
    client = get_client('eks', ctx.obj.get('region'))

    try:
        resp = client.describe_nodegroup(
            clusterName=cluster_name,
            nodegroupName=nodegroup_name
        )
        ng = resp['nodegroup']
    except ClientError as e:
        console.print(f"[red]Could not describe node group '{nodegroup_name}': {e}[/red]")
        return

    status_color = "green" if ng['status'] == 'ACTIVE' else "yellow"
    scaling = ng.get('scalingConfig', {})

    console.print(Panel(
        f"[bold cyan]{ng['nodegroupName']}[/bold cyan] on [cyan]{ng['clusterName']}[/cyan]",
        title="EKS Node Group"
    ))
    console.print(f"  Status:           [{status_color}]{ng['status']}[/{status_color}]")
    console.print(f"  K8s Version:      [green]{ng.get('version', 'N/A')}[/green]")
    console.print(f"  AMI Type:         {ng.get('amiType', 'N/A')}")
    console.print(f"  Release Version:  {ng.get('releaseVersion', 'N/A')}")
    console.print(f"  Instance Types:   {', '.join(ng.get('instanceTypes', []))}")
    console.print(f"  Capacity Type:    {ng.get('capacityType', 'N/A')}")
    console.print(f"  Disk Size:        {ng.get('diskSize', 'N/A')} GB")
    console.print(f"  ARN:              {ng.get('nodegroupArn', 'N/A')}")
    console.print(f"  Created:          {ng.get('createdAt', 'N/A')}")

    console.print(f"\n[bold]Scaling:[/bold]")
    console.print(f"  Desired:          {scaling.get('desiredSize', 'N/A')}")
    console.print(f"  Min:              {scaling.get('minSize', 'N/A')}")
    console.print(f"  Max:              {scaling.get('maxSize', 'N/A')}")

    console.print(f"\n[bold]Networking:[/bold]")
    console.print(f"  Subnets:          {', '.join(ng.get('subnets', []))}")

    remote = ng.get('remoteAccess', {})
    if remote:
        console.print(f"  SSH Key:          {remote.get('ec2SshKey', 'N/A')}")
        sgs = ', '.join(remote.get('sourceSecurityGroups', []))
        console.print(f"  SSH Sec Groups:   {sgs or 'N/A'}")

    labels = ng.get('labels', {})
    if labels:
        console.print(f"\n[bold]Labels:[/bold]")
        for key, value in labels.items():
            console.print(f"  {key}: [green]{value}[/green]")

    taints = ng.get('taints', [])
    if taints:
        console.print(f"\n[bold]Taints:[/bold]")
        for taint in taints:
            console.print(f"  {taint.get('key')}={taint.get('value', '')}:{taint.get('effect')}")

    health = ng.get('health', {})
    issues = health.get('issues', [])
    if issues:
        console.print(f"\n[bold red]Health Issues:[/bold red]")
        for issue in issues:
            console.print(f"  [{issue.get('code')}] {issue.get('message', 'N/A')}")


@eks.command('scale')
@click.argument('cluster_name')
@click.argument('nodegroup_name')
@click.option('--desired', type=int, required=True, help='Desired number of nodes')
@click.option('--min', 'min_size', type=int, default=None, help='Minimum number of nodes')
@click.option('--max', 'max_size', type=int, default=None, help='Maximum number of nodes')
@click.confirmation_option(prompt='Are you sure you want to scale this node group?')
@click.pass_context
def scale_nodegroup(ctx, cluster_name, nodegroup_name, desired, min_size, max_size):
    """Scale a node group (adjust desired/min/max)"""
    client = get_client('eks', ctx.obj.get('region'))

    scaling_config = {'desiredSize': desired}

    if min_size is not None:
        scaling_config['minSize'] = min_size
    if max_size is not None:
        scaling_config['maxSize'] = max_size

    if min_size is None or max_size is None:
        try:
            current = client.describe_nodegroup(
                clusterName=cluster_name,
                nodegroupName=nodegroup_name
            )['nodegroup']['scalingConfig']
            if min_size is None:
                scaling_config['minSize'] = current['minSize']
            if max_size is None:
                scaling_config['maxSize'] = current['maxSize']
        except ClientError as e:
            console.print(f"[red]Could not fetch current scaling config: {e}[/red]")
            return

    try:
        client.update_nodegroup_config(
            clusterName=cluster_name,
            nodegroupName=nodegroup_name,
            scalingConfig=scaling_config,
        )
        console.print(f"[green]Scaling {nodegroup_name} → desired={desired}, "
                       f"min={scaling_config['minSize']}, max={scaling_config['maxSize']}[/green]")
    except ClientError as e:
        console.print(f"[red]Failed to scale node group: {e}[/red]")


@eks.command('update')
@click.argument('cluster_name')
@click.option('--version', 'k8s_version', required=True, help='Target Kubernetes version (e.g. 1.29)')
@click.confirmation_option(prompt='Cluster updates can take 20+ minutes. Proceed?')
@click.pass_context
def update_cluster(ctx, cluster_name, k8s_version):
    """Update cluster Kubernetes version"""
    client = get_client('eks', ctx.obj.get('region'))

    try:
        resp = client.update_cluster_version(
            name=cluster_name,
            version=k8s_version,
        )
        update_id = resp['update']['id']
        console.print(f"[green]Cluster update started for '{cluster_name}' → v{k8s_version}[/green]")
        console.print(f"  Update ID: {update_id}")
        console.print(f"  This may take 20+ minutes. Check status with:")
        console.print(f"  [dim]devops-cli eks describe {cluster_name}[/dim]")
    except ClientError as e:
        console.print(f"[red]Failed to update cluster: {e}[/red]")


@eks.command('delete-nodegroup')
@click.argument('cluster_name')
@click.argument('nodegroup_name')
@click.confirmation_option(prompt='This will delete the node group and drain its nodes. Proceed?')
@click.pass_context
def delete_nodegroup(ctx, cluster_name, nodegroup_name):
    """Delete a node group from a cluster"""
    client = get_client('eks', ctx.obj.get('region'))

    with console.status(f"[bold red]Deleting node group {nodegroup_name}..."):
        try:
            client.delete_nodegroup(
                clusterName=cluster_name,
                nodegroupName=nodegroup_name,
            )
        except ClientError as e:
            console.print(f"[red]Failed to delete node group: {e}[/red]")
            return

    console.print(f"[yellow]Node group '{nodegroup_name}' deletion initiated.[/yellow]")
    console.print("  Nodes will be drained and terminated. This may take several minutes.")
    console.print(f"  Check status with: [dim]devops-cli eks nodegroups {cluster_name}[/dim]")


@eks.command('delete')
@click.argument('cluster_name')
@click.confirmation_option(prompt='THIS WILL DELETE THE ENTIRE CLUSTER. Are you absolutely sure?')
@click.pass_context
def delete_cluster(ctx, cluster_name):
    """Delete an EKS cluster (remove node groups first)"""
    client = get_client('eks', ctx.obj.get('region'))

    try:
        ngs = client.list_nodegroups(clusterName=cluster_name).get('nodegroups', [])
        if ngs:
            console.print(f"[red]Cluster still has node groups: {', '.join(ngs)}[/red]")
            console.print("Delete all node groups first before deleting the cluster.")
            return
    except ClientError as e:
        console.print(f"[red]AWS error: {e}[/red]")
        return

    try:
        client.delete_cluster(name=cluster_name)
        console.print(f"[yellow]Cluster '{cluster_name}' deletion initiated.[/yellow]")
        console.print("  This may take several minutes.")
    except ClientError as e:
        console.print(f"[red]Failed to delete cluster: {e}[/red]")

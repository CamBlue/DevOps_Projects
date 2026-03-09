import click
import boto3
import json

# ─────────────────────────────────────────
# ROOT CLI GROUP
# ─────────────────────────────────────────
@click.group()
def aws_cli():
    """AWS Resource Automation CLI"""
    pass

# ─────────────────────────────────────────
# EC2 GROUP
# ─────────────────────────────────────────
@aws_cli.group()
def ec2():
    """Manage EC2 instances"""
    pass

@ec2.command()
@click.option('--type', 'instance_type', default='t2.micro', help='Instance type')
@click.option('--name', required=True, help='Name tag for instance')
def launch(instance_type, name):
    """Launch a new EC2 instance (auto-fetches latest Amazon Linux 2023 AMI)"""
    ec2_client = boto3.client('ec2')

    # Auto-fetch latest Amazon Linux 2023 AMI for current region
    ami_response = ec2_client.describe_images(
        Owners=['amazon'],
        Filters=[
            {'Name': 'name', 'Values': ['al2023-ami-*-x86_64']},
            {'Name': 'state', 'Values': ['available']}
        ]
    )
    # Sort by creation date, grab the latest
    images = sorted(ami_response['Images'], key=lambda x: x['CreationDate'], reverse=True)
    ami_id = images[0]['ImageId']
    click.echo(f"  Using AMI: {ami_id}")

    # Launch instance
    resource = boto3.resource('ec2')
    instance = resource.create_instances(
        ImageId=ami_id,
        InstanceType=instance_type,
        MinCount=1,
        MaxCount=1,
        TagSpecifications=[{
            'ResourceType': 'instance',
            'Tags': [{'Key': 'Name', 'Value': name}]
        }]
    )[0]
    click.echo(f"✓ Launched instance: {instance.id}")


@ec2.command()
@click.option('--id', 'instance_id', required=True, help='Instance ID to terminate')
def terminate(instance_id):
    """Terminate an EC2 instance"""
    ec2_client = boto3.resource('ec2')
    instance = ec2_client.Instance(instance_id)
    instance.terminate()
    click.echo(f"✓ Terminating instance: {instance_id}")

@ec2.command(name='list')
@click.option('--state', default='running', 
              type=click.Choice(['running','stopped','terminated','all']),
              help='Filter by instance state')
def list_instances(state):
    """List EC2 instances"""
    ec2_client = boto3.client('ec2')
    filters = [] if state == 'all' else [{'Name': 'instance-state-name', 'Values': [state]}]
    response = ec2_client.describe_instances(Filters=filters)
    
    for reservation in response['Reservations']:
        for inst in reservation['Instances']:
            name = next((t['Value'] for t in inst.get('Tags', []) 
                        if t['Key'] == 'Name'), 'N/A')
            click.echo(f"  {inst['InstanceId']} | {inst['InstanceType']} | "
                      f"{inst['State']['Name']} | {name}")

@ec2.command()
@click.option('--id', 'instance_id', required=True, help='Instance ID to start')
def start(instance_id):
    """Start a stopped EC2 instance"""
    ec2_client = boto3.client('ec2')
    ec2_client.start_instances(InstanceIds=[instance_id])
    click.echo(f"✓ Starting instance: {instance_id}")

@ec2.command()
@click.option('--id', 'instance_id', required=True, help='Instance ID to stop')
def stop(instance_id):
    """Stop a running EC2 instance"""
    ec2_client = boto3.client('ec2')
    ec2_client.stop_instances(InstanceIds=[instance_id])
    click.echo(f"✓ Stopping instance: {instance_id}")

# ─────────────────────────────────────────
# S3 GROUP
# ─────────────────────────────────────────
@aws_cli.group()
def s3():
    """Manage S3 buckets"""
    pass

@s3.command()
@click.option('--name', required=True, help='Bucket name (must be globally unique)')
@click.option('--region', default=None, help='AWS region (defaults to your configured region)')
def create(name, region):
    """Create an S3 bucket"""
    s3_client = boto3.client('s3')

    # Auto-detect region if not specified
    if not region:
        region = boto3.session.Session().region_name

    click.echo(f"  Creating bucket '{name}' in region '{region}'...")

    if region == 'us-east-1':
        # us-east-1 does NOT use LocationConstraint (AWS quirk)
        s3_client.create_bucket(Bucket=name)
    else:
        # Every other region REQUIRES LocationConstraint
        s3_client.create_bucket(
            Bucket=name,
            CreateBucketConfiguration={'LocationConstraint': region}
        )

    click.echo(f"✓ Created bucket: {name}")


@s3.command()
@click.option('--name', required=True, help='Bucket name to delete')
def delete(name):
    """Delete an S3 bucket"""
    s3_client = boto3.resource('s3')
    bucket = s3_client.Bucket(name)
    bucket.objects.all().delete()  # Empty bucket first
    bucket.delete()
    click.echo(f"✓ Deleted bucket: {name}")

@s3.command(name='list')
def list_buckets():
    """List all S3 buckets"""
    s3_client = boto3.client('s3')
    response = s3_client.list_buckets()
    for bucket in response['Buckets']:
        click.echo(f"  {bucket['Name']} | Created: {bucket['CreationDate'].strftime('%Y-%m-%d')}")

@s3.command()
@click.option('--bucket', required=True, help='Bucket name')
@click.option('--file', 'file_path', required=True, help='Local file path to upload')
@click.option('--key', default=None, help='S3 object key (default: filename)')
def upload(bucket, file_path, key):
    """Upload a file to S3"""
    import os
    s3_client = boto3.client('s3')
    object_key = key or os.path.basename(file_path)
    s3_client.upload_file(file_path, bucket, object_key)
    click.echo(f"✓ Uploaded {file_path} → s3://{bucket}/{object_key}")

@s3.command()
@click.option('--bucket', required=True, help='Bucket name')
@click.option('--key', required=True, help='S3 object key to download')
@click.option('--output', required=True, help='Local path to save file')
def download(bucket, key, output):
    """Download a file from S3"""
    s3_client = boto3.client('s3')
    s3_client.download_file(bucket, key, output)
    click.echo(f"✓ Downloaded s3://{bucket}/{key} → {output}")

# ─────────────────────────────────────────
# LAMBDA GROUP
# ─────────────────────────────────────────
@aws_cli.group('lambda-func')
def lambda_func():
    """Manage Lambda functions"""
    pass

@lambda_func.command(name='list')
def list_functions():
    """List all Lambda functions"""
    lambda_client = boto3.client('lambda')
    response = lambda_client.list_functions()
    for fn in response['Functions']:
        click.echo(f"  {fn['FunctionName']} | {fn['Runtime']} | "
                  f"{fn['MemorySize']}MB | {fn['CodeSize']} bytes")

@lambda_func.command()
@click.option('--name', required=True, help='Lambda function name')
@click.option('--payload', default='{}', help='JSON payload string')
def invoke(name, payload):
    """Invoke a Lambda function"""
    import json
    
    lambda_client = boto3.client('lambda')
    
    # Fix payload - ensure it's valid JSON
    try:
        # Parse and re-serialize to guarantee valid JSON with proper quotes
        parsed = json.loads(payload)
        clean_payload = json.dumps(parsed)
    except json.JSONDecodeError:
        # If parsing fails, wrap it as a string value
        clean_payload = json.dumps({"input": payload})
    
    click.echo(f"  Invoking: {name}")
    click.echo(f"  Payload: {clean_payload}")
    
    response = lambda_client.invoke(
        FunctionName=name,
        Payload=clean_payload.encode('utf-8')
    )
    
    result = json.loads(response['Payload'].read())
    click.echo(f"✓ Status: {response['StatusCode']}")
    click.echo(f"✓ Response: {json.dumps(result, indent=2)}")


# ─────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────
if __name__ == '__main__':
    aws_cli()

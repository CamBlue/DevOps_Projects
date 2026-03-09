# AWS Lambda Cost Optimizer

## Project Overview
**Difficulty:** Intermediate  
**Estimated Time:** 3-4 hours  
**Skills Practiced:** Python, AWS Lambda, EventBridge, Cost Optimization, Boto3

### What You'll Build
An AWS Lambda function that automatically:
- Stops non-production EC2 instances on weekends
- Starts them back up on Monday mornings
- Identifies and reports unused EBS volumes
- Finds unattached Elastic IPs costing money
- Detects old snapshots that can be deleted
- Sends cost savings reports via email/Slack

### Why This Matters
Cloud costs can spiral quickly. This project teaches you to build automated cost optimization—reducing AWS bills by 30-50% for non-production environments while maintaining production availability.

### Prerequisites
- AWS account with billing access
- AWS CLI installed and configured
- Python 3.8+ installed
- IAM permissions for Lambda, EC2, CloudWatch Events

---

## Step-by-Step Implementation

### Step 1: Set Up AWS Prerequisites

**1. Create IAM Policy for Lambda**

Go to AWS Console → IAM → Policies → Create Policy

Switch to JSON tab and paste:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeInstances",
                "ec2:DescribeVolumes",
                "ec2:DescribeSnapshots",
                "ec2:DescribeAddresses",
                "ec2:StartInstances",
                "ec2:StopInstances",
                "ec2:DescribeTags",
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "sns:Publish"
            ],
            "Resource": "*"
        }
    ]
}
```

Name it: `LambdaCostOptimizerPolicy`

**2. Create IAM Role for Lambda**

Go to IAM → Roles → Create Role
- Trusted entity: AWS Service → Lambda
- Attach policy: `LambdaCostOptimizerPolicy`
- Role name: `LambdaCostOptimizerRole`

**3. Set Up SNS Topic for Notifications**

```bash
# Create SNS topic
aws sns create-topic --name cost-optimizer-alerts

# Subscribe your email
aws sns subscribe \
    --topic-arn arn:aws:sns:us-east-1:ACCOUNT_ID:cost-optimizer-alerts \
    --protocol email \
    --notification-endpoint your-email@example.com

# Confirm subscription in your email
```

### Step 2: Create Test EC2 Instances

**Create instances with proper tags for testing:**

```bash
# Launch a test instance
aws ec2 run-instances \
    --image-id ami-0c55b159cbfafe1f0 \
    --instance-type t2.micro \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=dev-test-server},{Key=Environment,Value=dev},{Key=AutoStop,Value=true}]' \
    --count 1

# Verify it's running
aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=dev-test-server" \
    --query 'Reservations[*].Instances[*].[InstanceId,State.Name,Tags[?Key==`Name`].Value|[0]]' \
    --output table
```

**Tagging strategy for cost optimization:**
- `Environment=dev|staging|prod` - Identifies environment
- `AutoStop=true` - Marks instances eligible for auto-shutdown
- `Name=descriptive-name` - Human-readable identifier

### Step 3: Write Lambda Function Code

Create `lambda_function.py`:
```python
import boto3
import json
from datetime import datetime, timedelta
import os

ec2 = boto3.client('ec2')
sns = boto3.client('sns')

def lambda_handler(event, context):
    """Main Lambda handler"""
    action = event.get('action', 'stop')  # 'stop' or 'start'

    results = {
        'action': action,
        'timestamp': datetime.now().isoformat(),
        'instances_processed': [],
        'cost_savings': []
    }

    if action == 'stop':
        results['instances_processed'] = stop_dev_instances()
        results['cost_savings'] = identify_cost_savings()
    elif action == 'start':
        results['instances_processed'] = start_dev_instances()

    # Send notification
    send_notification(results)

    return {
        'statusCode': 200,
        'body': json.dumps(results, default=str)
    }

def stop_dev_instances():
    """Stop non-production instances tagged for auto-stop"""
    stopped_instances = []

    # Find instances to stop
    filters = [
        {'Name': 'tag:AutoStop', 'Values': ['true']},
        {'Name': 'instance-state-name', 'Values': ['running']}
    ]

    response = ec2.describe_instances(Filters=filters)

    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            instance_name = get_instance_name(instance)
            env = get_tag_value(instance, 'Environment')

            # Only stop dev/staging, never prod
            if env in ['dev', 'staging']:
                try:
                    ec2.stop_instances(InstanceIds=[instance_id])
                    stopped_instances.append({
                        'instance_id': instance_id,
                        'name': instance_name,
                        'environment': env
                    })
                    print(f"✓ Stopped: {instance_name} ({instance_id})")
                except Exception as e:
                    print(f"✗ Error stopping {instance_id}: {e}")

    return stopped_instances

def start_dev_instances():
    """Start instances that were auto-stopped"""
    started_instances = []

    filters = [
        {'Name': 'tag:AutoStop', 'Values': ['true']},
        {'Name': 'instance-state-name', 'Values': ['stopped']}
    ]

    response = ec2.describe_instances(Filters=filters)

    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            instance_name = get_instance_name(instance)
            env = get_tag_value(instance, 'Environment')

            if env in ['dev', 'staging']:
                try:
                    ec2.start_instances(InstanceIds=[instance_id])
                    started_instances.append({
                        'instance_id': instance_id,
                        'name': instance_name,
                        'environment': env
                    })
                    print(f"✓ Started: {instance_name} ({instance_id})")
                except Exception as e:
                    print(f"✗ Error starting {instance_id}: {e}")

    return started_instances

def identify_cost_savings():
    """Identify resources costing money unnecessarily"""
    savings = []

    # Find unattached EBS volumes
    volumes = ec2.describe_volumes(
        Filters=[{'Name': 'status', 'Values': ['available']}]
    )

    for volume in volumes['Volumes']:
        size_gb = volume['Size']
        monthly_cost = size_gb * 0.10  # ~$0.10 per GB-month for gp3

        savings.append({
            'type': 'Unattached Volume',
            'resource_id': volume['VolumeId'],
            'monthly_cost': monthly_cost,
            'recommendation': 'Delete if not needed'
        })

    # Find unattached Elastic IPs
    addresses = ec2.describe_addresses()
    for address in addresses['Addresses']:
        if 'InstanceId' not in address:
            savings.append({
                'type': 'Unattached Elastic IP',
                'resource_id': address.get('AllocationId', 'N/A'),
                'public_ip': address['PublicIp'],
                'monthly_cost': 3.60,  # $0.005/hour
                'recommendation': 'Release if not needed'
            })

    # Find old snapshots (older than 90 days)
    cutoff_date = datetime.now() - timedelta(days=90)
    snapshots = ec2.describe_snapshots(OwnerIds=['self'])

    for snapshot in snapshots['Snapshots']:
        if snapshot['StartTime'].replace(tzinfo=None) < cutoff_date:
            size_gb = snapshot['VolumeSize']
            monthly_cost = size_gb * 0.05  # $0.05 per GB-month for snapshots

            savings.append({
                'type': 'Old Snapshot',
                'resource_id': snapshot['SnapshotId'],
                'age_days': (datetime.now() - snapshot['StartTime'].replace(tzinfo=None)).days,
                'size_gb': size_gb,
                'monthly_cost': monthly_cost,
                'recommendation': 'Review and delete if obsolete'
            })

    return savings

def get_instance_name(instance):
    """Extract Name tag from instance"""
    for tag in instance.get('Tags', []):
        if tag['Key'] == 'Name':
            return tag['Value']
    return 'Unnamed'

def get_tag_value(instance, tag_key):
    """Get specific tag value from instance"""
    for tag in instance.get('Tags', []):
        if tag['Key'] == tag_key:
            return tag['Value']
    return None

def send_notification(results):
    """Send results via SNS"""
    topic_arn = os.environ.get('SNS_TOPIC_ARN')
    if not topic_arn:
        print("No SNS topic configured")
        return

    action = results['action']
    instances = results['instances_processed']
    savings = results['cost_savings']

    if action == 'stop':
        subject = f"Cost Optimizer: Stopped {len(instances)} instances"
        message = f"""
Cost Optimization Report
========================

Stopped Instances: {len(instances)}

Instances:
"""
        for inst in instances:
            message += f"  - {inst['name']} ({inst['instance_id']}) [{inst['environment']}]\n"

        if savings:
            total_monthly_savings = sum(s.get('monthly_cost', 0) for s in savings)
            message += f"""

Potential Cost Savings: ${total_monthly_savings:.2f}/month

Recommendations:
"""
            for save in savings[:10]:  # Top 10
                message += f"  - {save['type']}: {save['resource_id']} (${save['monthly_cost']:.2f}/mo)\n"

    else:  # start
        subject = f"Cost Optimizer: Started {len(instances)} instances"
        message = f"""
Cost Optimizer: Monday Startup
===============================

Started Instances: {len(instances)}

Instances:
"""
        for inst in instances:
            message += f"  - {inst['name']} ({inst['instance_id']}) [{inst['environment']}]\n"

    try:
        sns.publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=message
        )
        print("✓ Notification sent")
    except Exception as e:
        print(f"✗ Error sending notification: {e}")
```

### Step 4: Package Lambda Function

```bash
# Create deployment package
mkdir lambda-package
cd lambda-package

# Copy function code
cp ../lambda_function.py .

# Create ZIP
zip -r lambda_function.zip lambda_function.py

# Verify contents
unzip -l lambda_function.zip
```

### Step 5: Deploy Lambda Function

**Using AWS CLI:**
```bash
# Get your account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Get SNS topic ARN
SNS_ARN="arn:aws:sns:us-east-1:${ACCOUNT_ID}:cost-optimizer-alerts"

# Create Lambda function
aws lambda create-function \
    --function-name cost-optimizer \
    --runtime python3.11 \
    --role arn:aws:iam::${ACCOUNT_ID}:role/LambdaCostOptimizerRole \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://lambda_function.zip \
    --timeout 300 \
    --memory-size 256 \
    --environment "Variables={SNS_TOPIC_ARN=${SNS_ARN}}"

# Verify deployment
aws lambda get-function --function-name cost-optimizer
```

**Using AWS Console:**
1. Go to Lambda → Create function
2. Function name: `cost-optimizer`
3. Runtime: Python 3.11
4. Execution role: Use existing role → LambdaCostOptimizerRole
5. Upload `lambda_function.zip`
6. Set environment variable: `SNS_TOPIC_ARN` = your SNS topic ARN
7. Set timeout: 5 minutes
8. Click "Deploy"

### Step 6: Create EventBridge Schedules

**Schedule to stop instances (Friday 6 PM):**
```bash
# Create rule for Friday shutdown
aws events put-rule \
    --name stop-dev-instances-friday \
    --schedule-expression "cron(0 18 ? * FRI *)" \
    --description "Stop dev instances every Friday at 6 PM"

# Add Lambda as target
aws events put-targets \
    --rule stop-dev-instances-friday \
    --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:${ACCOUNT_ID}:function:cost-optimizer","Input"='{"action":"stop"}'

# Grant EventBridge permission to invoke Lambda
aws lambda add-permission \
    --function-name cost-optimizer \
    --statement-id AllowEventBridgeStop \
    --action lambda:InvokeFunction \
    --principal events.amazonaws.com \
    --source-arn arn:aws:events:us-east-1:${ACCOUNT_ID}:rule/stop-dev-instances-friday
```

**Schedule to start instances (Monday 8 AM):**
```bash
# Create rule for Monday startup
aws events put-rule \
    --name start-dev-instances-monday \
    --schedule-expression "cron(0 8 ? * MON *)" \
    --description "Start dev instances every Monday at 8 AM"

# Add Lambda as target
aws events put-targets \
    --rule start-dev-instances-monday \
    --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:${ACCOUNT_ID}:function:cost-optimizer","Input"='{"action":"start"}'

# Grant permission
aws lambda add-permission \
    --function-name cost-optimizer \
    --statement-id AllowEventBridgeStart \
    --action lambda:InvokeFunction \
    --principal events.amazonaws.com \
    --source-arn arn:aws:events:us-east-1:${ACCOUNT_ID}:rule/start-dev-instances-monday
```

**Using AWS Console:**
1. Go to EventBridge → Rules → Create rule
2. Name: `stop-dev-instances-friday`
3. Rule type: Schedule
4. Schedule pattern: Cron expression → `0 18 ? * FRI *`
5. Target: Lambda function → cost-optimizer
6. Configure input: Constant (JSON) → `{"action":"stop"}`
7. Create rule

Repeat for Monday startup with `cron(0 8 ? * MON *)` and `{"action":"start"}`

### Step 7: Test Lambda Function

**Manual test via Console:**
1. Go to Lambda → cost-optimizer → Test
2. Create test event:
```json
{
  "action": "stop"
}
```
3. Click "Test"
4. Check execution results and CloudWatch logs

**Manual test via CLI:**
```bash
# Test stop action
aws lambda invoke \
    --function-name cost-optimizer \
    --payload '{"action":"stop"}' \
    response.json

# Check results
cat response.json | python -m json.tool

# Test start action
aws lambda invoke \
    --function-name cost-optimizer \
    --payload '{"action":"start"}' \
    response.json
```

**Verify instances were stopped:**
```bash
aws ec2 describe-instances \
    --filters "Name=tag:AutoStop,Values=true" \
    --query 'Reservations[*].Instances[*].[InstanceId,State.Name,Tags[?Key==`Name`].Value|[0]]' \
    --output table
```

### Step 8: Monitor with CloudWatch Logs

```bash
# View recent logs
aws logs tail /aws/lambda/cost-optimizer --follow

# Check for errors
aws logs filter-log-events \
    --log-group-name /aws/lambda/cost-optimizer \
    --filter-pattern "ERROR"

# Get metrics
aws cloudwatch get-metric-statistics \
    --namespace AWS/Lambda \
    --metric-name Invocations \
    --dimensions Name=FunctionName,Value=cost-optimizer \
    --start-time $(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 3600 \
    --statistics Sum
```

### Step 9: Calculate Cost Savings

**Create cost calculator script:**
```python
# cost_calculator.py
def calculate_ec2_savings(instance_type, hours_saved_per_week=60):
    """Calculate weekly savings from stopping instances"""

    # EC2 on-demand pricing (us-east-1)
    pricing = {
        't2.micro': 0.0116,
        't2.small': 0.023,
        't2.medium': 0.0464,
        't3.micro': 0.0104,
        't3.small': 0.0208,
        't3.medium': 0.0416,
    }

    hourly_rate = pricing.get(instance_type, 0.0464)
    weekly_savings = hourly_rate * hours_saved_per_week
    monthly_savings = weekly_savings * 4.33  # Average weeks per month
    annual_savings = monthly_savings * 12

    print(f"Instance Type: {instance_type}")
    print(f"Hourly Rate: ${hourly_rate}")
    print(f"Hours Saved/Week: {hours_saved_per_week}")
    print(f"Weekly Savings: ${weekly_savings:.2f}")
    print(f"Monthly Savings: ${monthly_savings:.2f}")
    print(f"Annual Savings: ${annual_savings:.2f}")

# Example: 5 t3.medium instances stopped 60 hours/week
calculate_ec2_savings('t3.medium', 60)
# Result: ~$108/month, ~$1,296/year per instance
```

### Step 10: Clean Up Resources

**When done testing:**
```bash
# Delete EventBridge rules
aws events remove-targets --rule stop-dev-instances-friday --ids 1
aws events delete-rule --name stop-dev-instances-friday
aws events remove-targets --rule start-dev-instances-monday --ids 1
aws events delete-rule --name start-dev-instances-monday

# Delete Lambda function
aws lambda delete-function --function-name cost-optimizer

# Terminate test instances
aws ec2 terminate-instances --instance-ids <your-test-instance-id>

# Delete SNS topic
aws sns delete-topic --topic-arn arn:aws:sns:us-east-1:ACCOUNT_ID:cost-optimizer-alerts

# Delete IAM role and policy
aws iam detach-role-policy --role-name LambdaCostOptimizerRole --policy-arn arn:aws:iam::ACCOUNT_ID:policy/LambdaCostOptimizerPolicy
aws iam delete-role --role-name LambdaCostOptimizerRole
aws iam delete-policy --policy-arn arn:aws:iam::ACCOUNT_ID:policy/LambdaCostOptimizerPolicy
```

---

## Success Criteria
- [ ] Lambda function successfully stops tagged instances
- [ ] EventBridge schedules trigger function automatically
- [ ] SNS notifications delivered with cost savings report
- [ ] Identifies unattached volumes and Elastic IPs
- [ ] CloudWatch logs show successful execution
- [ ] Cost savings calculated and verified

## Extension Ideas
1. **RDS Instances:** Stop/start RDS databases on schedule
2. **Auto Scaling Groups:** Reduce ASG capacity on weekends
3. **Cost Dashboard:** Build CloudWatch dashboard with savings
4. **Slack Integration:** Send reports to Slack instead of email
5. **Rightsizing:** Recommend smaller instance types based on utilization
6. **Reserved Instance Analysis:** Identify RI optimization opportunities
7. **Multi-Region:** Extend to all AWS regions

## Common Issues

**Issue:** Lambda times out  
**Solution:** Increase timeout to 5 minutes in configuration

**Issue:** Permission denied errors  
**Solution:** Verify IAM role has all required EC2 permissions

**Issue:** Instances not stopping  
**Solution:** Check AutoStop tag is spelled correctly and set to "true"

**Issue:** No SNS notification received  
**Solution:** Confirm email subscription and check spam folder

## Cost Breakdown

**Lambda costs (minimal):**
- 1M requests free per month
- Typical usage: ~60 invocations/month = FREE

**Potential savings:**
- 5x t3.medium stopped 60 hrs/week = **~$540/month saved**
- Deleted 100GB unused volumes = **~$10/month saved**
- Released 2 unused Elastic IPs = **~$7/month saved**

**Total potential savings: $557/month = $6,684/year**

---

**Completion Time:** 3-4 hours  
**Difficulty:** Intermediate  
**AWS Costs:** Minimal (free tier eligible)  
**Next Category:** Infrastructure as Code

# AWS Resource Automation with Boto3

## Project Overview
**Difficulty:** Beginner  
**Estimated Time:** 3-4 hours  
**Skills Practiced:** Python, AWS SDK (Boto3), AWS EC2, S3, Lambda

### What You'll Build
A modular Python CLI tool that automates common AWS tasks including:
- Launching and terminating EC2 instances
- Creating and managing S3 buckets
- Deploying and invoking Lambda functions
- Listing and filtering AWS resources

### Why This Matters
Boto3 is the AWS SDK for Python and is essential for any DevOps engineer working with AWS. This project teaches you how to programmatically manage cloud resources instead of clicking through the AWS Console—a critical automation skill.

### Prerequisites
- AWS account (free tier is sufficient)
- AWS CLI installed and configured with credentials
- Python 3.8+ installed
- Basic understanding of EC2, S3, and Lambda concepts

---

## Step-by-Step Implementation

### Step 1: Set Up Your Project Structure
```bash
mkdir aws-resource-automation
cd aws-resource-automation
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
pip install boto3 click
```

**What's Happening:**
- Creating isolated Python environment to avoid dependency conflicts
- Installing `boto3` (AWS SDK) and `click` (CLI framework)

### Step 2: Configure AWS Credentials
```bash
aws configure
```

**Enter your credentials when prompted:**
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., `us-east-1`)
- Default output format: `json`

**Verify configuration:**
```bash
aws sts get-caller-identity
```

### Step 3: Create the Project File Structure
```
aws-resource-automation/
├── README.md
├── requirements.txt
├── aws_automation/
│   ├── __init__.py
│   ├── ec2_manager.py
│   ├── s3_manager.py
│   ├── lambda_manager.py
│   └── utils.py
├── cli.py
└── config.yaml
```

Create this structure:
```bash
mkdir aws_automation
touch aws_automation/{__init__.py,ec2_manager.py,s3_manager.py,lambda_manager.py,utils.py}
touch cli.py requirements.txt config.yaml README.md
```

### Step 4: Implement EC2 Manager

Create `aws_automation/ec2_manager.py` with the following functionality:

**Core Methods to Implement:**
1. `__init__(self, region)` - Initialize boto3 client and resource
2. `launch_instance()` - Launch new EC2 instances with tags
3. `terminate_instance()` - Terminate instances by ID
4. `list_instances()` - List all instances with filters
5. `start_instance()` - Start stopped instances
6. `stop_instance()` - Stop running instances

**Key Implementation Points:**
- Use `boto3.client('ec2')` for API calls
- Use `boto3.resource('ec2')` for object-oriented access
- Wrap all AWS calls in try/except blocks with `ClientError`
- Return instance IDs and handle responses properly
- Add Name tags for better organization

**Example Code Structure:**
```python
import boto3
from botocore.exceptions import ClientError

class EC2Manager:
    def __init__(self, region='us-east-1'):
        self.ec2_client = boto3.client('ec2', region_name=region)
        self.ec2_resource = boto3.resource('ec2', region_name=region)

    def launch_instance(self, ami_id, instance_type='t2.micro', 
                       key_name=None, name_tag=None):
        # Implementation here
        pass
```

### Step 5: Implement S3 Manager

Create `aws_automation/s3_manager.py` with these operations:

**Core Methods:**
1. `create_bucket()` - Create new S3 buckets with region handling
2. `delete_bucket()` - Delete buckets (with force option for non-empty)
3. `upload_file()` - Upload files to bucket
4. `download_file()` - Download files from bucket
5. `list_buckets()` - List all buckets in account
6. `list_objects()` - List objects in specific bucket

**Important Notes:**
- us-east-1 bucket creation doesn't need LocationConstraint
- Other regions require CreateBucketConfiguration
- Use `bucket.objects.all().delete()` for force deletion
- Bucket names must be globally unique

### Step 6: Implement Lambda Manager

Create `aws_automation/lambda_manager.py`:

**Core Methods:**
1. `create_function()` - Deploy Lambda from zip file
2. `invoke_function()` - Execute Lambda with optional payload
3. `delete_function()` - Remove Lambda function
4. `list_functions()` - List all functions in region
5. `create_zip_from_file()` - Helper to package Python files

**Lambda-Specific Considerations:**
- Code must be provided as zip file
- Requires IAM role ARN with Lambda execution permissions
- Handler format: `filename.function_name`
- Common runtimes: python3.9, python3.10, python3.11

### Step 7: Build the CLI Interface

Create `cli.py` using Click framework:

**CLI Structure:**
```
aws-cli
├── ec2
│   ├── launch
│   ├── terminate
│   ├── list
│   ├── start
│   └── stop
├── s3
│   ├── create
│   ├── delete
│   ├── list
│   ├── upload
│   └── download
└── lambda-func
    ├── list
    └── invoke
```

**Implementation Pattern:**
```python
import click
from aws_automation.ec2_manager import EC2Manager

@click.group()
def cli():
    pass

@cli.group()
def ec2():
    '''Manage EC2 instances'''
    pass

@ec2.command()
@click.option('--ami', required=True, help='AMI ID')
@click.option('--type', default='t2.micro')
def launch(ami, type):
    manager = EC2Manager()
    manager.launch_instance(ami, instance_type=type)
```

### Step 8: Create Requirements and README

**requirements.txt:**
```
boto3==1.34.51
click==8.1.7
botocore==1.34.51
```

**README.md should include:**
- Project description
- Installation instructions
- Configuration steps
- Usage examples for each command
- Common troubleshooting tips

### Step 9: Test Your Implementation

**Test EC2 Operations:**
```bash
# List instances
python cli.py ec2 list

# Launch instance (use your region's AMI)
python cli.py ec2 launch --ami ami-0c55b159cbfafe1f0 --name TestServer

# Stop instance
python cli.py ec2 stop i-1234567890abcdef0
```

**Test S3 Operations:**
```bash
# Create bucket with unique name
python cli.py s3 create my-test-bucket-$(date +%s)

# Upload test file
echo "test data" > test.txt
python cli.py s3 upload test.txt my-test-bucket-<timestamp>

# List buckets
python cli.py s3 list

# Delete bucket
python cli.py s3 delete my-test-bucket-<timestamp> --force
```

**Test Lambda Operations:**
```bash
# List existing functions
python cli.py lambda-func list

# Invoke a function
python cli.py lambda-func invoke my-function --payload '{"key":"value"}'
```

### Step 10: Clean Up Resources

**IMPORTANT:** Always clean up to avoid charges:
```bash
# Terminate all test instances
python cli.py ec2 terminate <instance-id>

# Delete all test buckets
python cli.py s3 delete <bucket-name> --force

# Delete test Lambda functions
# (add delete command to CLI if not implemented)
```

---

## Success Criteria
- [ ] CLI tool successfully launches and terminates EC2 instances
- [ ] Can create S3 buckets and upload/download files
- [ ] Proper error handling for invalid inputs and AWS errors
- [ ] Code is modular with separate manager classes
- [ ] README includes clear usage examples
- [ ] All AWS resources properly cleaned up after testing

## Extension Ideas
1. **Add Filtering:** Filter EC2 instances by tags, state, or instance type
2. **Bulk Operations:** Terminate multiple instances at once
3. **S3 Sync:** Implement directory sync to/from S3
4. **CloudWatch Integration:** Fetch Lambda logs and EC2 metrics
5. **Cost Estimation:** Calculate estimated costs for operations
6. **Configuration File:** YAML config for default settings
7. **Unit Tests:** Use pytest and moto to mock AWS services

## Common Issues & Troubleshooting

**Issue:** `NoCredentialsError: Unable to locate credentials`  
**Solution:** Run `aws configure` and ensure credentials are set

**Issue:** `AccessDenied` when calling AWS APIs  
**Solution:** Verify IAM user has required permissions (EC2FullAccess, S3FullAccess, etc.)

**Issue:** `BucketAlreadyExists` when creating S3 bucket  
**Solution:** Bucket names are globally unique—add timestamp or random suffix

**Issue:** `InvalidAMIID.NotFound`  
**Solution:** AMI IDs are region-specific—use an AMI from your configured region

**Issue:** Lambda creation fails with `InvalidParameterValueException`  
**Solution:** Ensure IAM role has Lambda execution trust policy

## Learning Resources
- [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [AWS CLI Reference](https://awscli.amazonaws.com/v2/documentation/api/latest/index.html)
- [Click Documentation](https://click.palletsprojects.com/)
- [AWS Free Tier](https://aws.amazon.com/free/)

---

**Completion Time:** 3-4 hours  
**Difficulty:** Beginner  
**Next Project:** Server Health Check Script

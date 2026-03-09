import boto3
from botocore.exceptions import ClientError

class EC2Manager:
    def __init__(self, region='us-east-1'):
        self.ec2 = boto3.client('ec2', region_name=region)
        self.ec2_resource= boto3.resource('ec2', region_name=region) 

    def launch_instance(self, ami_id, instance_type='t2.micro', 
                        key_name=None, name_tag=None): 
        pass



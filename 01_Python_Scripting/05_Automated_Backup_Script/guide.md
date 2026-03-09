# Automated Backup Script

## Project Overview
**Difficulty:** Beginner-Intermediate  
**Estimated Time:** 3 hours  
**Skills Practiced:** Python, AWS S3, Scheduling, Error Handling

### What You'll Build
A Python script that:
- Backs up databases (MySQL, PostgreSQL) and file systems
- Uploads backups to AWS S3 with encryption
- Implements backup rotation (keep last N backups)
- Sends notifications on success/failure
- Logs all backup operations
- Supports scheduled execution

### Why This Matters
Automated backups are critical for disaster recovery. This project teaches you to build reliable backup systems with proper rotation policies—preventing data loss and ensuring business continuity.

---

## Step-by-Step Implementation

### Step 1: Project Setup
```bash
mkdir automated-backup
cd automated-backup
python3 -m venv venv
source venv/bin/activate
pip install boto3 pymysql psycopg2-binary python-dotenv schedule
```

### Step 2: Implement Database Backup
```python
import subprocess
import os
from datetime import datetime

class DatabaseBackup:
    def backup_mysql(self, host, user, password, database, output_dir):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{database}_mysql_{timestamp}.sql"
        filepath = os.path.join(output_dir, filename)

        cmd = f"mysqldump -h {host} -u {user} -p{password} {database} > {filepath}"
        subprocess.run(cmd, shell=True, check=True)
        return filepath

    def backup_postgresql(self, host, user, password, database, output_dir):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{database}_postgres_{timestamp}.sql"
        filepath = os.path.join(output_dir, filename)

        os.environ['PGPASSWORD'] = password
        cmd = f"pg_dump -h {host} -U {user} {database} > {filepath}"
        subprocess.run(cmd, shell=True, check=True)
        return filepath
```

### Step 3: Implement S3 Upload
```python
import boto3
from botocore.exceptions import ClientError

class S3Uploader:
    def __init__(self, bucket_name):
        self.s3_client = boto3.client('s3')
        self.bucket_name = bucket_name

    def upload_file(self, file_path, s3_key=None):
        if s3_key is None:
            s3_key = os.path.basename(file_path)

        try:
            self.s3_client.upload_file(
                file_path, 
                self.bucket_name, 
                s3_key,
                ExtraArgs={'ServerSideEncryption': 'AES256'}
            )
            return True
        except ClientError as e:
            print(f"Upload failed: {e}")
            return False

    def list_backups(self, prefix=''):
        response = self.s3_client.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=prefix
        )
        return response.get('Contents', [])

    def delete_old_backups(self, prefix, keep_count=7):
        backups = self.list_backups(prefix)
        backups.sort(key=lambda x: x['LastModified'], reverse=True)

        # Delete older backups beyond keep_count
        for backup in backups[keep_count:]:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=backup['Key']
            )
            print(f"Deleted old backup: {backup['Key']}")
```

### Step 4: Implement File System Backup
```python
import tarfile

def backup_directory(source_dir, output_dir):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"filesystem_{timestamp}.tar.gz"
    filepath = os.path.join(output_dir, filename)

    with tarfile.open(filepath, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))

    return filepath
```

### Step 5: Add Logging and Notifications
```python
import logging
import requests

logging.basicConfig(
    filename='backup.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def send_notification(success, backup_name, error=None):
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')

    if success:
        message = f"✓ Backup successful: {backup_name}"
        color = "good"
    else:
        message = f"✗ Backup failed: {backup_name}\nError: {error}"
        color = "danger"

    payload = {
        "attachments": [{
            "color": color,
            "text": message
        }]
    }

    requests.post(webhook_url, json=payload)
```

### Step 6: Create Main Backup Orchestrator
```python
def main():
    try:
        # Create temp backup directory
        backup_dir = '/tmp/backups'
        os.makedirs(backup_dir, exist_ok=True)

        # Backup MySQL database
        db_backup = DatabaseBackup()
        mysql_file = db_backup.backup_mysql(
            host='localhost',
            user='root',
            password=os.getenv('MYSQL_PASSWORD'),
            database='myapp',
            output_dir=backup_dir
        )
        logging.info(f"MySQL backup created: {mysql_file}")

        # Upload to S3
        uploader = S3Uploader('my-backup-bucket')
        success = uploader.upload_file(mysql_file, f"mysql/{os.path.basename(mysql_file)}")

        if success:
            logging.info("Backup uploaded to S3")
            uploader.delete_old_backups('mysql/', keep_count=7)
            send_notification(True, mysql_file)
        else:
            raise Exception("S3 upload failed")

        # Cleanup local backup
        os.remove(mysql_file)

    except Exception as e:
        logging.error(f"Backup failed: {e}")
        send_notification(False, "MySQL backup", str(e))
```

### Step 7: Add Scheduling
```python
import schedule
import time

def scheduled_backup():
    print(f"Running backup at {datetime.now()}")
    main()

# Schedule daily at 2 AM
schedule.every().day.at("02:00").do(scheduled_backup)

# Schedule every 6 hours
# schedule.every(6).hours.do(scheduled_backup)

print("Backup scheduler started. Press Ctrl+C to stop.")
while True:
    schedule.run_pending()
    time.sleep(60)
```

### Step 8: Test Your Implementation
```bash
# Test single backup
python backup_script.py

# Test with scheduling
python backup_scheduler.py
```

---

## Success Criteria
- [ ] Successfully backs up MySQL/PostgreSQL databases
- [ ] Uploads backups to S3 with encryption
- [ ] Implements backup rotation (keeps last 7)
- [ ] Sends notifications on success/failure
- [ ] Logs all operations
- [ ] Can run on schedule

## Extension Ideas
1. **Multi-Database Support:** Backup multiple databases in one run
2. **Compression:** Add compression before upload
3. **Incremental Backups:** Only backup changed data
4. **Backup Verification:** Restore and verify backup integrity
5. **Cloud Provider Support:** Add Azure Blob, GCP Storage
6. **Monitoring Dashboard:** Track backup status over time

---

**Completion Time:** 3 hours  
**Difficulty:** Beginner-Intermediate  
**Next Project:** Kubernetes API Interaction

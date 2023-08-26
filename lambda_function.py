#!/usr/bin/env python
import json
import logging
from datetime import datetime
import boto3
from botocore.exceptions import ClientError


def save_metrics(session, log, metrics, bucket='uc-6-metrics'):
    str_current_datetime = str(datetime.now().strftime("%Y-%m-%d %H-%M-%S"))
    file_key  = str_current_datetime+".json"
    
    datastr = json.dumps(metrics, indent=2, default=str)
    try:
        client = session.client("s3")
        client.put_object(Bucket=bucket, Key="metrics/"+file_key, Body=datastr)
    except ClientError as e:
        log.error(f"Upload to s3 has been failed: {e}")

def lambda_handler(event, context):
    uc6 = boto3.session.Session()
    log = logging.getLogger()
    ec2 = uc6.client('ec2')
    try:
        aws_account_id = uc6.client("sts").get_caller_identity()["Account"]
        volumes = ec2.describe_volumes()['Volumes']
        unattached_volumes = [d['Size'] for d in volumes if 'attached' not in map(lambda w: w['State'], d['Attachments'])]
        nonencrypted = ec2.describe_volumes(Filters=[{'Name': 'encrypted', 'Values': ['false']},])['Volumes']
        nonencrypted_volumes = [d['Size'] for d in  nonencrypted]
        snaps = ec2.describe_snapshots(Filters=[{'Name': 'encrypted', 'Values': ['false']},
                                                {'Name': 'owner-id', 'Values': [aws_account_id]}])['Snapshots']
        snapshots = [d['VolumeSize'] for d in snaps]
    except ClientError as e:
        log.error(f"Connection hasn't been established: {e}")

    core_keys = [unattached_volumes, nonencrypted_volumes, snapshots]
    data = {}
    for k in core_keys:
        k_name = [i for i, j in locals().items() if j == k][0]
        data[k_name] = {}
        data[k_name]['Number'] = len(k)
        data[k_name]['Sizes'] = k

    save_metrics(uc6, log, data)

if __name__ == '__main__':

    lambda_handler("","")

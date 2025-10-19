#!/usr/bin/env python3

import os
import logging
from typing import List
import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

def get_ec2_client(region: str = None):
    """
    Creates a Boto3 EC2 client.
    """
    region = region or os.getenv("AWS_REGION", "us-east-1")
    return boto3.client("ec2", region_name=region)


def get_instances_to_stop(ec2_client) -> List[str]:
    """
    Returns a list of instance IDs that have the tag AutoStop=true and are running.
    """
    try:
        response = ec2_client.describe_instances(
            Filters=[
                {'Name': 'tag:AutoStop', 'Values': ['true']},
                {'Name': 'instance-state-name', 'Values': ['running']}
            ]
        )

        instance_ids = [
            instance['InstanceId']
            for reservation in response.get('Reservations', [])
            for instance in reservation.get('Instances', [])
        ]
        return instance_ids

    except (BotoCoreError, ClientError) as e:
        logger.error(f"Failed to describe instances: {e}")
        return []


def stop_instances(ec2_client, instance_ids: List[str]) -> None:
    """
    Stops the given list of EC2 instances.
    """
    if not instance_ids:
        logger.info("No instances to stop.")
        return

    try:
        logger.info(f"Stopping instances: {instance_ids}")
        ec2_client.stop_instances(InstanceIds=instance_ids)
        logger.info("Stop command issued successfully.")

    except (BotoCoreError, ClientError) as e:
        logger.error(f"Failed to stop instances: {e}")


def main():
    ec2_client = get_ec2_client()
    instances_to_stop = get_instances_to_stop(ec2_client)
    stop_instances(ec2_client, instances_to_stop)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import os
import time
import logging
from typing import Optional, List
import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def get_logs_client(region: Optional[str] = None):
    """
    Initializes and returns a Boto3 CloudWatch Logs client.
    """
    region = region or os.getenv("AWS_REGION", "us-east-1")
    return boto3.client('logs', region_name=region)


def get_recent_log_streams(logs_client, log_group: str, limit: int = 5) -> List[str]:
    """
    Returns the most recent log stream names from a given log group.
    """
    try:
        response = logs_client.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=limit
        )
        return [stream['logStreamName'] for stream in response.get('logStreams', [])]

    except (BotoCoreError, ClientError) as e:
        logger.error(f"Error fetching log streams: {e}")
        return []


def scan_logs_for_pattern(
    logs_client,
    log_group: str,
    log_streams: List[str],
    filter_pattern: str = 'ERROR',
    lookback_minutes: int = 60
):
    """
    Scans the provided log streams for the given pattern within the specified time window.
    """
    now = int(time.time() * 1000)
    start_time = now - (lookback_minutes * 60 * 1000)

    for stream in log_streams:
        try:
            response = logs_client.filter_log_events(
                logGroupName=log_group,
                logStreamNames=[stream],
                startTime=start_time,
                endTime=now,
                filterPattern=filter_pattern
            )

            for event in response.get('events', []):
                message = event.get('message', '').strip()
                logger.warning(f"[{stream}] {message}")

        except (BotoCoreError, ClientError) as e:
            logger.error(f"Error scanning log stream {stream}: {e}")


def main():
    log_group = os.getenv("LOG_GROUP_NAME", "/aws/lambda/your-log-group-name")
    region = os.getenv("AWS_REGION", "us-east-1")
    filter_pattern = os.getenv("FILTER_PATTERN", "ERROR")

    logs_client = get_logs_client(region)
    log_streams = get_recent_log_streams(logs_client, log_group)

    if not log_streams:
        logger.info("No recent log streams found.")
        return

    scan_logs_for_pattern(logs_client, log_group, log_streams, filter_pattern)


if __name__ == "__main__":
    main()

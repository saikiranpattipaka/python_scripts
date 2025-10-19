#!/usr/bin/env python3

import os
import shutil
import smtplib
import logging
from typing import Optional
from email.mime.text import MIMEText
from email.utils import formatdate
from dotenv import load_dotenv

# Load environment variables from .env (optional)
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def get_disk_usage(path: str = "/") -> float:
    """
    Returns disk usage as a percentage for the given path.
    """
    total, used, _ = shutil.disk_usage(path)
    return (used / total) * 100


def send_email_alert(usage: float) -> None:
    """
    Sends an alert email if disk usage exceeds threshold.
    """
    sender = os.getenv("ALERT_EMAIL_FROM", "devops@yourdomain.com")
    recipient = os.getenv("ALERT_EMAIL_TO", "admin@yourdomain.com")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.yourdomain.com")
    smtp_port = int(os.getenv("SMTP_PORT", 25))
    smtp_user = os.getenv("SMTP_USERNAME")
    smtp_pass = os.getenv("SMTP_PASSWORD")

    subject = "🚨 Disk Space Alert"
    body = f"Disk usage is critically high: {usage:.2f}%"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg["Date"] = formatdate(localtime=True)

    try:
        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
            server.ehlo()
            if smtp_user and smtp_pass:
                server.starttls()
                server.login(smtp_user, smtp_pass)

            server.send_message(msg)
            logger.warning(f"Disk usage alert sent: {usage:.2f}%")
    except Exception as e:
        logger.error(f"Failed to send alert email: {e}")


def check_and_alert(threshold: float = 80.0, path: str = "/") -> None:
    """
    Checks disk usage and sends an alert if above the threshold.
    """
    usage = get_disk_usage(path)
    logger.info(f"Disk usage at {usage:.2f}% (threshold: {threshold}%)")

    if usage > threshold:
        send_email_alert(usage)
    else:
        logger.info("Disk usage within safe limits.")


if __name__ == "__main__":
    threshold_env = os.getenv("DISK_USAGE_THRESHOLD", "80")
    path_env = os.getenv("DISK_USAGE_PATH", "/")

    try:
        threshold = float(threshold_env)
    except ValueError:
        logger.error("Invalid threshold value. Using default: 80")
        threshold = 80.0

    check_and_alert(threshold, path_env)

from __future__ import annotations

import json
import os
from typing import Any, Dict

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from ...core.config import Settings
from ...core.logging_config import get_logger

logger = get_logger(__name__)


def load_secrets_into_env(settings: Settings) -> Dict[str, Any]:
    """
    Fetch secret payload from AWS Secrets Manager and merge into environment variables.

    Authentication:
    Boto3 uses the default credential chain to authenticate with AWS. Credentials are resolved
    in the following order (first available is used):
    1. Environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN (optional)
    2. AWS credentials file: ~/.aws/credentials
    3. AWS config file: ~/.aws/config
    4. IAM roles (if running on EC2/ECS/Lambda)
    5. IAM instance profile

    Required environment variables:
    - AWS_REGION: AWS region where the secret is stored (e.g., 'us-east-1')
    - AWS_SECRETS_MANAGER_SECRET_NAME: Name or ARN of the secret in AWS Secrets Manager

    Optional environment variables for authentication (if not using IAM roles):
    - AWS_ACCESS_KEY_ID: AWS access key ID
    - AWS_SECRET_ACCESS_KEY: AWS secret access key
    - AWS_SESSION_TOKEN: AWS session token (required for temporary credentials)

    Returns the decoded secret payload.
    """
    # Boto3 automatically discovers credentials using the default credential chain
    # No explicit credentials need to be passed here
    session = boto3.session.Session(region_name=settings.aws_region)
    client = session.client("secretsmanager")

    try:
        response = client.get_secret_value(SecretId=settings.aws_secret_name)
    except (ClientError, BotoCoreError) as exc:
        logger.warning("Unable to retrieve secrets from AWS", extra={"error": str(exc)})
        raise

    secret_string = response.get("SecretString")
    if not secret_string:
        logger.warning("SecretString missing in AWS response", extra={"secret_name": settings.aws_secret_name})
        return {}

    secrets: Dict[str, Any] = json.loads(secret_string)
    for key, value in secrets.items():
        os.environ.setdefault(key, str(value))

    logger.info("Loaded secrets into environment", extra={"secret_name": settings.aws_secret_name})
    return secrets



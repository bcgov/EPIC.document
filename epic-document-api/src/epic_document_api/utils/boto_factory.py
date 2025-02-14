"""The factory implementation of the boto3 library."""

import boto3
from botocore.config import Config
from flask import current_app


class Boto3ClientFactory:
    """Boto3ClientFactory."""

    def __init__(
        self,
        region_name: str = None,
        endpoint_url: str = None,
        max_retries: int = 3,
        timeout: int = 60,
    ):
        """
        Initialize the Boto3 client factory.

        :param aws_access_key: AWS Access Key ID (Optional, uses default if None)
        :param aws_secret_key: AWS Secret Access Key (Optional, uses default if None)
        :param region_name: AWS region to use (default: "us-east-1")
        :param endpoint_url: Custom endpoint URL (useful for local testing like LocalStack)
        :param max_retries: Maximum retry attempts for API calls
        :param timeout: Request timeout in seconds
        """
        self.aws_access_key = current_app.config.get("S3_ACCESS_KEY_ID")
        self.aws_secret_key = current_app.config.get("S3_SECRET_ACCESS_KEY")
        self.region_name = region_name or current_app.config.get("S3_REGION")
        self.endpoint_url = endpoint_url
        self.config = Config(
            retries={"max_attempts": max_retries, "mode": "standard"},
            connect_timeout=timeout,
            read_timeout=timeout,
        )

    def get_client(self, service_name: str):
        """
        Create a Boto3 client for a given AWS service.

        :param service_name: Name of the AWS service (e.g., "s3", "dynamodb", "sns")
        :return: Boto3 client instance
        """
        client_params = {
            "service_name": service_name,
            "region_name": self.region_name,
            "config": self.config,
        }

        # Add credentials only if explicitly provided
        if self.aws_access_key and self.aws_secret_key:
            client_params["aws_access_key_id"] = self.aws_access_key
            client_params["aws_secret_access_key"] = self.aws_secret_key

        # Override endpoint URL if provided (useful for LocalStack, MinIO, etc.)
        if self.endpoint_url:
            client_params["endpoint_url"] = self.endpoint_url

        return boto3.client(**client_params)

import logging
import os
from typing import BinaryIO

import boto3
from botocore.exceptions import ClientError

try:
    from api.config import get_settings
except Exception:  # workers context may import storage without API
    get_settings = None  # type: ignore

logger = logging.getLogger(__name__)


class ObjectStore:
    def __init__(self) -> None:
        if get_settings:
            try:
                settings = get_settings()
                self.endpoint = settings.s3_endpoint or os.getenv(
                    "S3_ENDPOINT", "http://minio:9000"
                )
                self.region = settings.s3_region or os.getenv("S3_REGION", "us-east-1")
                self.bucket = settings.s3_bucket or os.getenv("S3_BUCKET", "promoai")
            except Exception:
                self.endpoint = os.getenv("S3_ENDPOINT", "http://minio:9000")
                self.region = os.getenv("S3_REGION", "us-east-1")
                self.bucket = os.getenv("S3_BUCKET", "promoai")
        else:
            self.endpoint = os.getenv("S3_ENDPOINT", "http://minio:9000")
            self.region = os.getenv("S3_REGION", "us-east-1")
            self.bucket = os.getenv("S3_BUCKET", "promoai")

        # Check for S3 credentials
        if get_settings:
            try:
                self.access_key = settings.s3_access_key_id or os.getenv("S3_ACCESS_KEY_ID")  # type: ignore[name-defined]
                self.secret_key = settings.s3_secret_access_key or os.getenv("S3_SECRET_ACCESS_KEY")  # type: ignore[name-defined]
            except Exception:
                self.access_key = os.getenv("S3_ACCESS_KEY_ID")
                self.secret_key = os.getenv("S3_SECRET_ACCESS_KEY")
        else:
            self.access_key = os.getenv("S3_ACCESS_KEY_ID")
            self.secret_key = os.getenv("S3_SECRET_ACCESS_KEY")

        if not self.access_key or not self.secret_key:
            logger.warning(
                "S3_ACCESS_KEY_ID or S3_SECRET_ACCESS_KEY not set. "
                "Using default MinIO credentials for local development."
            )
            self.access_key = self.access_key or "minio"
            self.secret_key = self.secret_key or "minio123"

        # Initialize S3 client
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            region_name=self.region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            use_ssl=False,  # For local MinIO
        )

        # Ensure bucket exists (best-effort)
        try:
            self.ensure_bucket()
        except Exception:
            # In dev environments MinIO may be initializing; ignore on init
            pass

    def ensure_bucket(self) -> None:
        """Ensure the bucket exists, create if it doesn't."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket)
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                # Bucket doesn't exist, create it
                self.s3_client.create_bucket(Bucket=self.bucket)
            else:
                raise

    def put_file(self, local_path: str, dest_key: str) -> str:
        """Upload a file to S3 and return the S3 URI."""
        try:
            self.s3_client.upload_file(local_path, self.bucket, dest_key)
            return f"s3://{self.bucket}/{dest_key}"
        except ClientError as e:
            raise Exception(f"Failed to upload file: {e}") from e

    def put_data(self, data: BinaryIO, dest_key: str) -> str:
        """Upload data from file-like object to S3 and return the S3 URI."""
        try:
            self.s3_client.upload_fileobj(data, self.bucket, dest_key)
            return f"s3://{self.bucket}/{dest_key}"
        except ClientError as e:
            raise Exception(f"Failed to upload data: {e}") from e

    def get_file(self, key: str, dest_path: str) -> None:
        """Download a file from S3 to local path."""
        try:
            self.s3_client.download_file(self.bucket, key, dest_path)
        except ClientError as e:
            raise Exception(f"Failed to download file: {e}") from e

    def get_data(self, key: str) -> bytes:
        """Download data from S3 and return as bytes."""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
            body = response["Body"]
            if body is None:
                raise Exception("Empty response body")
            data = body.read()
            if isinstance(data, bytes):
                return data
            else:
                return data.encode("utf-8")
        except ClientError as e:
            raise Exception(f"Failed to download data: {e}") from e

    def delete(self, key: str) -> bool:
        """Delete a file from S3."""
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError as e:
            logger.warning(f"Failed to delete {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if a file exists in S3."""
        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                return False
            raise


# Backward compatibility
class R2Storage(ObjectStore):
    """Legacy class name for backward compatibility."""

    pass

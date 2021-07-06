import os
from typing import Any, Optional

import boto3
import botocore
from structlog import get_logger
from tenacity import retry

from modelkit.assets import errors
from modelkit.assets.drivers.abc import StorageDriver
from modelkit.assets.drivers.retry import RETRY_POLICY

logger = get_logger(__name__)


class S3StorageDriver(StorageDriver):
    bucket: str
    endpoint_url: Optional[str]
    client: Any

    def __init__(
        self,
        bucket: str = None,
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None,
        aws_default_region: str = None,
        aws_session_token: str = None,
        s3_endpoint: str = None,
    ):

        self.bucket = bucket or os.environ.get("MODELKIT_STORAGE_BUCKET", None)
        if bucket is None:
            raise ValueError("Bucket needs to be set for S3 storage driver")
        self.endpoint_url = s3_endpoint or os.environ.get("S3_ENDPOINT", None)
        self.client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=aws_access_key_id
            or os.environ.get("AWS_ACCESS_KEY_ID", None),
            aws_secret_access_key=aws_secret_access_key
            or os.environ.get("AWS_SECRET_ACCESS_KEY", None),
            aws_session_token=aws_session_token
            or os.environ.get("AWS_SESSION_TOKEN", None),
            region_name=aws_default_region
            or os.environ.get("AWS_DEFAULT_REGION", None),
        )

    @retry(**RETRY_POLICY)
    def iterate_objects(self, prefix=None):
        paginator = self.client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=self.bucket, Prefix=prefix or "")
        for page in pages:
            for obj in page.get("Contents", []):
                yield obj["Key"]

    @retry(**RETRY_POLICY)
    def upload_object(self, file_path, object_name):
        self.client.upload_file(file_path, self.bucket, object_name)

    @retry(**RETRY_POLICY)
    def download_object(self, object_name, destination_path):
        try:
            with open(destination_path, "wb") as f:
                self.client.download_fileobj(self.bucket, object_name, f)
        except botocore.exceptions.ClientError:
            logger.error(
                "Object not found.", bucket=self.bucket, object_name=object_name
            )
            os.remove(destination_path)
            raise errors.ObjectDoesNotExistError(
                driver=self, bucket=self.bucket, object_name=object_name
            )

    @retry(**RETRY_POLICY)
    def delete_object(self, object_name):
        self.client.delete_object(Bucket=self.bucket, Key=object_name)

    @retry(**RETRY_POLICY)
    def exists(self, object_name):
        try:
            self.client.head_object(Bucket=self.bucket, Key=object_name)
            return True
        except botocore.exceptions.ClientError:
            return False

    def __repr__(self):
        return f"<S3StorageDriver endpoint_url={self.endpoint_url}>"

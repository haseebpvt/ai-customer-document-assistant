import os

import boto3


def download(key: str) -> bytes:
    return boto3.client("s3").get_object(
        Bucket=os.environ["S3_BUCKET"],
        Key=key,
    )["Body"].read()

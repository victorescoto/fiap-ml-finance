import os
import boto3
from functools import lru_cache

PREFIX = os.getenv("APP_PREFIX", "fiap-fase3")
REGION = os.getenv("AWS_REGION", "us-east-2")
RAW_BUCKET = f"fiap-fase3-finance-raw"
MODELS_BUCKET = f"fiap-fase3-finance-models"


@lru_cache(maxsize=1)
def s3_client():
    return boto3.client("s3", region_name=REGION)

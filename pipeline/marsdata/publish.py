"""Uploads data/regions/ to Cloudflare R2 (S3-compatible API)."""

import mimetypes
import os
from pathlib import Path

import boto3

from marsdata.export import OUT_DIR

mimetypes.add_type("application/geo+json", ".geojson")
mimetypes.add_type("application/octet-stream", ".npy")


def r2_client():
    return boto3.client(
        "s3",
        endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
    )


def publish(src: Path = OUT_DIR, prefix: str = "regions") -> int:
    bucket = os.environ.get("R2_BUCKET", "wazemars-assets")
    client = r2_client()
    count = 0
    for path in sorted(p for p in src.rglob("*") if p.is_file()):
        key = f"{prefix}/{path.relative_to(src).as_posix()}"
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        client.upload_file(str(path), bucket, key, ExtraArgs={"ContentType": content_type})
        count += 1
    return count

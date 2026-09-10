#!/usr/bin/env python3
"""Cloudflare R2 image upload utility for clip-note.

Uploads local image assets to Cloudflare R2 bucket and returns the public CDN URL.
Credentials and domain should be configured via environment variables or in ~/.config/clip-note/r2.env:
- R2_ENDPOINT
- R2_ACCESS_KEY_ID
- R2_SECRET_ACCESS_KEY
- R2_BUCKET (default: obsidian)
- R2_PREFIX (default: interpreter-image)
- R2_PUBLIC_DOMAIN (e.g. https://pub-<id>.r2.dev)
"""

from __future__ import annotations
import os
import sys
import site
import mimetypes
from pathlib import Path

# Ensure user site-packages is searched (e.g. Homebrew Python on macOS)
user_site = site.getusersitepackages()
if os.path.exists(user_site) and user_site not in sys.path:
    sys.path.insert(0, user_site)

try:
    import boto3
    from botocore.config import Config
except ImportError:
    print("Error: boto3 is required for R2 upload. Run: pip install boto3", file=sys.stderr)
    sys.exit(1)


def load_env_file():
    """Load configuration from ~/.config/clip-note/r2.env if present."""
    config_file = Path.home() / ".config" / "clip-note" / "r2.env"
    if config_file.exists():
        try:
            for line in config_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip().strip("\"'")
                if k not in os.environ:
                    os.environ[k] = v
        except Exception:
            pass


load_env_file()

R2_ENDPOINT = os.environ.get("R2_ENDPOINT", "")
R2_ACCESS_KEY_ID = os.environ.get("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.environ.get("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET = os.environ.get("R2_BUCKET", "obsidian")
R2_PREFIX = os.environ.get("R2_PREFIX", "interpreter-image")
PUBLIC_DOMAIN = os.environ.get("R2_PUBLIC_DOMAIN", "").rstrip("/")


def get_s3_client():
    if not R2_ACCESS_KEY_ID or not R2_SECRET_ACCESS_KEY or not R2_ENDPOINT or not PUBLIC_DOMAIN:
        raise ValueError(
            "R2 credentials or public domain are not configured.\n"
            "Please set R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, and R2_PUBLIC_DOMAIN in your environment,\n"
            "or put them in ~/.config/clip-note/r2.env"
        )
    return boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def upload_file(file_path: str | Path, key_name: str | None = None) -> str:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    filename = key_name or path.name
    object_key = f"{R2_PREFIX}/{filename}"

    content_type, _ = mimetypes.guess_type(str(path))
    if not content_type:
        content_type = "image/jpeg"

    client = get_s3_client()
    extra_args = {"ContentType": content_type}

    with open(path, "rb") as f:
        client.upload_fileobj(f, R2_BUCKET, object_key, ExtraArgs=extra_args)

    return f"{PUBLIC_DOMAIN}/{object_key}"


def upload_bytes(data: bytes, filename: str, content_type: str = "image/jpeg") -> str:
    object_key = f"{R2_PREFIX}/{filename}"
    client = get_s3_client()
    extra_args = {"ContentType": content_type}
    
    client.put_object(
        Bucket=R2_BUCKET,
        Key=object_key,
        Body=data,
        ContentType=content_type,
    )
    return f"{PUBLIC_DOMAIN}/{object_key}"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 r2_upload.py <file1> [file2 ...]")
        sys.exit(1)

    for arg in sys.argv[1:]:
        try:
            url = upload_file(arg)
            print(f"Uploaded: {arg} -> {url}")
        except Exception as e:
            print(f"Failed to upload {arg}: {e}", file=sys.stderr)
            sys.exit(1)

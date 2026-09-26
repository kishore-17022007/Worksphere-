"""S3-compatible file storage abstraction (metadata is kept in SQL only)."""
from dataclasses import dataclass
from typing import BinaryIO
import uuid

@dataclass
class StoredObject:
    key: str
    size: int
    content_type: str

class ObjectStorage:
    async def put(self, stream: BinaryIO, *, key: str, content_type: str) -> StoredObject:
        raise NotImplementedError
    def download_url(self, key: str, expires: int = 3600) -> str:
        raise NotImplementedError

class S3Storage(ObjectStorage):
    """Adapter contract; applications can inject boto3/aiobotocore implementation."""
    def __init__(self, bucket: str, endpoint_url: str | None = None):
        self.bucket, self.endpoint_url = bucket, endpoint_url
    async def put(self, stream: BinaryIO, *, key: str, content_type: str) -> StoredObject:
        data = stream.read()
        return StoredObject(key, len(data), content_type)
    def download_url(self, key: str, expires: int = 3600) -> str:
        base = self.endpoint_url or f"https://{self.bucket}.s3.amazonaws.com"
        return f"{base.rstrip('/')}/{key}"

def object_key(company_id: uuid.UUID, filename: str) -> str:
    return f"{company_id}/{uuid.uuid4()}-{filename}"

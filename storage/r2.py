import os
from typing import BinaryIO, Optional


class R2Storage:
    def __init__(self) -> None:
        self.endpoint = os.getenv("S3_ENDPOINT", "http://minio:9000")
        self.region = os.getenv("S3_REGION", "us-east-1")
        self.bucket = os.getenv("S3_BUCKET", "promoai")
        self.access_key = os.getenv("S3_ACCESS_KEY_ID")
        self.secret_key = os.getenv("S3_SECRET_ACCESS_KEY")

    def put(self, key: str, data: BinaryIO) -> bool:
        # TODO: Implement actual R2 upload
        print(f"Would upload {key} to R2")
        return True

    def get(self, key: str) -> Optional[bytes]:
        # TODO: Implement actual R2 download
        print(f"Would download {key} from R2")
        return None

    def delete(self, key: str) -> bool:
        # TODO: Implement actual R2 deletion
        print(f"Would delete {key} from R2")
        return True

"""Storage service for media file uploads to Qiniu Cloud."""
import os
from typing import BinaryIO

from qiniu import Auth, put_file, put_data
from qiniu import BucketManager

from app.config import get_settings

settings = get_settings()


class StorageService:
    """Service for managing file uploads to Qiniu Cloud."""

    def __init__(self) -> None:
        self.access_key = settings.qiniu_access_key
        self.secret_key = settings.qiniu_secret_key
        self.bucket_name = settings.qiniu_bucket
        self.domain = settings.qiniu_domain

        if self.access_key and self.secret_key:
            self.auth = Auth(self.access_key, self.secret_key)
            self.bucket_manager = BucketManager(self.auth)
            self._enabled = True
        else:
            self._enabled = False

    def is_enabled(self) -> bool:
        """Check if storage service is properly configured."""
        return self._enabled

    def generate_token(self, key: str) -> str:
        """Generate upload token for a file key."""
        if not self.is_enabled():
            raise RuntimeError("Storage service is not configured")
        return self.auth.upload_token(self.bucket_name, key, 3600)

    def generate_file_key(self, filename: str, user_id: int) -> str:
        """Generate a unique file key for storage."""
        ext = os.path.splitext(filename)[1]
        return f"publify/{user_id}/{os.urandom(8).hex()}{ext}"

    async def upload_file(
        self, file_data: BinaryIO, filename: str, user_id: int
    ) -> str | None:
        """Upload a file and return its public URL."""
        if not self.is_enabled():
            return None

        try:
            key = self.generate_file_key(filename, user_id)
            token = self.generate_token(key)

            # Read file data
            file_data.seek(0)
            data = file_data.read()

            # Upload to Qiniu
            ret, info = put_data(token, key, data)

            if ret and info.status_code == 200:
                return f"{self.domain}/{key}"
            return None

        except Exception as e:
            # Log error in production
            return None

    async def delete_file(self, url: str) -> bool:
        """Delete a file from storage."""
        if not self.is_enabled():
            return False

        try:
            # Extract key from URL
            if self.domain in url:
                key = url.replace(f"{self.domain}/", "")
            else:
                return False

            # Delete from Qiniu
            ret, info = self.bucket_manager.delete(self.bucket_name, key)
            return info.status_code == 200

        except Exception as e:
            # Log error in production
            return False

    def validate_image(self, filename: str, size: int) -> tuple[bool, str]:
        """Validate an image file."""
        allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}
        ext = os.path.splitext(filename)[1].lower()

        if ext not in allowed_extensions:
            return False, f"Invalid image format. Allowed: {', '.join(allowed_extensions)}"

        if size > 10 * 1024 * 1024:  # 10MB
            return False, "Image size exceeds 10MB limit"

        return True, ""

    def validate_video(self, filename: str, size: int) -> tuple[bool, str]:
        """Validate a video file."""
        allowed_extensions = {".mp4"}
        ext = os.path.splitext(filename)[1].lower()

        if ext not in allowed_extensions:
            return False, "Invalid video format. Only MP4 is allowed"

        if size > 100 * 1024 * 1024:  # 100MB
            return False, "Video size exceeds 100MB limit"

        return True, ""


# Global instance
storage_service = StorageService()

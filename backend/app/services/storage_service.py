"""
Storage service interface and local filesystem implementation.
Abstracted to allow seamless replacement with Amazon S3 or Google Cloud Storage.
"""
import os
import aiofiles
from app.core.config import settings
from app.utils.logger import logger


class StorageService:
    def __init__(self, base_dir: str = settings.STORAGE_DIR):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    async def save_file(self, filename: str, content: bytes) -> str:
        """Save file bytes and return relative path."""
        file_path = os.path.join(self.base_dir, filename)
        # Ensure parent dir exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        logger.info(f"File saved successfully: {file_path}")
        return file_path

    async def read_file(self, file_path: str) -> bytes:
        """Read file contents as bytes."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        async with aiofiles.open(file_path, "rb") as f:
            return await f.read()

    async def delete_file(self, file_path: str) -> bool:
        """Delete file if it exists."""
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"File deleted: {file_path}")
            return True
        return False


storage_service = StorageService()

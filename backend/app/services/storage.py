import os
import uuid
import logging
from typing import Tuple
from pathlib import Path
from app.core.config import settings

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        # We will use local storage for local development/docker and prepare for Cloudflare R2/S3
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.use_s3 = False  # Set to True if S3 variables are configured in settings in future

    async def save_file(self, file_content: bytes, original_filename: str) -> Tuple[str, int]:
        """Save a file to the storage system. Returns a tuple: (file_url, file_size_in_bytes)."""
        file_size = len(file_content)
        
        # Clean/sanitize filename and prepend a UUID to guarantee uniqueness
        ext = os.path.splitext(original_filename)[1]
        unique_filename = f"{uuid.uuid4()}{ext}"
        
        if self.use_s3:
            # Placeholder for S3/R2 upload logic (boto3)
            # In Phase 1 MVP, we use the local storage stub, easily replaceable for R2
            pass
            
        # Local Storage Fallback
        file_path = self.upload_dir / unique_filename
        with open(file_path, "wb") as f:
            f.write(file_content)
            
        # Return local static URL path (which we will serve in main.py)
        file_url = f"/api/v1/resumes/download/{unique_filename}"
        logger.info(f"File saved successfully to local disk: {file_path} (size: {file_size} bytes)")
        
        return file_url, file_size

    async def delete_file(self, file_url: str) -> bool:
        """Delete file from local disk if it exists."""
        try:
            filename = os.path.basename(file_url)
            file_path = self.upload_dir / filename
            if file_path.exists():
                file_path.unlink()
                logger.info(f"File deleted successfully from storage: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete file {file_url}: {str(e)}")
            return False

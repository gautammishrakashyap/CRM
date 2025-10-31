import boto3
import uuid
from typing import Optional, BinaryIO, Tuple
from datetime import datetime
from fastapi import HTTPException, UploadFile
from botocore.exceptions import ClientError, NoCredentialsError
from app.core.config import (
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, S3_BUCKET_NAME,
    S3_UPLOAD_ENABLED, MAX_UPLOAD_SIZE, ALLOWED_IMAGE_EXTENSIONS, ALLOWED_DOCUMENT_EXTENSIONS
)
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class S3UploadService:
    """Service for handling file uploads to AWS S3"""
    
    def __init__(self):
        self.s3_enabled = S3_UPLOAD_ENABLED
        self.bucket_name = S3_BUCKET_NAME
        self.max_file_size = MAX_UPLOAD_SIZE
        self.allowed_image_ext = ALLOWED_IMAGE_EXTENSIONS
        self.allowed_document_ext = ALLOWED_DOCUMENT_EXTENSIONS
        
        if self.s3_enabled:
            try:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                    region_name=AWS_REGION
                )
                logger.info("S3 client initialized successfully")
            except (NoCredentialsError, Exception) as e:
                logger.error(f"Failed to initialize S3 client: {str(e)}")
                self.s3_enabled = False
        else:
            logger.info("S3 upload is disabled, using local storage")
            # Create local upload directory
            self.local_upload_dir = Path("uploads")
            self.local_upload_dir.mkdir(exist_ok=True)
    
    def validate_file(self, file: UploadFile, file_type: str = "image") -> Tuple[bool, str]:
        """Validate file size and extension"""
        try:
            # Check file size
            if file.size and file.size > self.max_file_size:
                return False, f"File size exceeds maximum limit of {self.max_file_size / (1024*1024):.1f}MB"
            
            # Check file extension
            if not file.filename:
                return False, "Filename is required"
            
            file_extension = file.filename.split('.')[-1].lower()
            
            if file_type == "image":
                allowed_extensions = self.allowed_image_ext
            elif file_type == "document":
                allowed_extensions = self.allowed_document_ext
            else:
                allowed_extensions = self.allowed_image_ext + self.allowed_document_ext
            
            if file_extension not in allowed_extensions:
                return False, f"File extension '{file_extension}' not allowed. Allowed: {', '.join(allowed_extensions)}"
            
            return True, "File is valid"
            
        except Exception as e:
            logger.error(f"Error validating file: {str(e)}")
            return False, f"Error validating file: {str(e)}"
    
    def generate_unique_filename(self, original_filename: str, user_id: str, category: str) -> str:
        """Generate unique filename for upload"""
        file_extension = original_filename.split('.')[-1].lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"{category}/{user_id}/{timestamp}_{unique_id}.{file_extension}"
    
    async def upload_file_to_s3(self, file: UploadFile, s3_key: str) -> Optional[str]:
        """Upload file to S3 bucket"""
        try:
            # Read file content
            file_content = await file.read()
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=file.content_type or 'application/octet-stream'
            )
            
            # Generate public URL
            file_url = f"https://{self.bucket_name}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
            logger.info(f"File uploaded to S3: {file_url}")
            return file_url
            
        except ClientError as e:
            logger.error(f"AWS S3 error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"S3 upload failed: {str(e)}")
        except Exception as e:
            logger.error(f"Error uploading to S3: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    
    async def upload_file_locally(self, file: UploadFile, file_path: str) -> Optional[str]:
        """Upload file to local storage (fallback when S3 is disabled)"""
        try:
            # Create directory if it doesn't exist
            file_full_path = self.local_upload_dir / file_path
            file_full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save file content
            file_content = await file.read()
            with open(file_full_path, "wb") as f:
                f.write(file_content)
            
            # Return relative URL (assuming you have a static file server)
            file_url = f"/uploads/{file_path}"
            logger.info(f"File uploaded locally: {file_url}")
            return file_url
            
        except Exception as e:
            logger.error(f"Error uploading locally: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Local upload failed: {str(e)}")
    
    async def upload_profile_image(self, file: UploadFile, user_id: str) -> dict:
        """Upload student profile image"""
        try:
            # Validate file
            is_valid, message = self.validate_file(file, "image")
            if not is_valid:
                raise HTTPException(status_code=400, detail=message)
            
            # Generate unique filename
            filename = self.generate_unique_filename(file.filename, user_id, "profile_images")
            
            # Upload file
            if self.s3_enabled:
                file_url = await self.upload_file_to_s3(file, filename)
            else:
                file_url = await self.upload_file_locally(file, filename)
            
            return {
                "file_url": file_url,
                "file_name": file.filename,
                "file_size": file.size or 0,
                "upload_timestamp": datetime.utcnow(),
                "category": "profile_image"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error uploading profile image: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to upload profile image")
    
    async def upload_document(self, file: UploadFile, user_id: str, category: str) -> dict:
        """Upload student document"""
        try:
            # Validate file
            is_valid, message = self.validate_file(file, "document")
            if not is_valid:
                raise HTTPException(status_code=400, detail=message)
            
            # Generate unique filename
            filename = self.generate_unique_filename(file.filename, user_id, f"documents/{category}")
            
            # Upload file
            if self.s3_enabled:
                file_url = await self.upload_file_to_s3(file, filename)
            else:
                file_url = await self.upload_file_locally(file, filename)
            
            return {
                "file_url": file_url,
                "file_name": file.filename,
                "file_size": file.size or 0,
                "upload_timestamp": datetime.utcnow(),
                "category": category
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to upload document")
    
    def delete_file_from_s3(self, file_url: str) -> bool:
        """Delete file from S3 bucket"""
        try:
            if not self.s3_enabled or not file_url:
                return False
            
            # Extract S3 key from URL
            # Assuming URL format: https://bucket.s3.region.amazonaws.com/key
            if f"{self.bucket_name}.s3." in file_url:
                s3_key = file_url.split(f"{self.bucket_name}.s3.{AWS_REGION}.amazonaws.com/")[1]
                
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
                logger.info(f"File deleted from S3: {s3_key}")
                return True
            
            return False
            
        except ClientError as e:
            logger.error(f"Error deleting file from S3: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            return False
    
    def delete_file_locally(self, file_url: str) -> bool:
        """Delete file from local storage"""
        try:
            if not file_url or not file_url.startswith("/uploads/"):
                return False
            
            # Extract relative path
            relative_path = file_url.replace("/uploads/", "")
            file_path = self.local_upload_dir / relative_path
            
            if file_path.exists():
                file_path.unlink()
                logger.info(f"File deleted locally: {file_path}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting local file: {str(e)}")
            return False
    
    def delete_file(self, file_url: str) -> bool:
        """Delete file (S3 or local based on configuration)"""
        if self.s3_enabled:
            return self.delete_file_from_s3(file_url)
        else:
            return self.delete_file_locally(file_url)
    
    def get_upload_config(self) -> dict:
        """Get upload configuration for frontend"""
        return {
            "s3_enabled": self.s3_enabled,
            "max_file_size": self.max_file_size,
            "max_file_size_mb": self.max_file_size / (1024 * 1024),
            "allowed_image_extensions": self.allowed_image_ext,
            "allowed_document_extensions": self.allowed_document_ext,
            "bucket_name": self.bucket_name if self.s3_enabled else None
        }


# Global instance
s3_service = S3UploadService()


def get_s3_service() -> S3UploadService:
    """Dependency to get S3 upload service"""
    return s3_service
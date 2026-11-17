import os
import uuid
import mimetypes
from pathlib import Path
from typing import Optional, Dict, Any, BinaryIO, Union
from logging import getLogger

import boto3
from botocore.exceptions import ClientError
from botocore.config import Config

logger = getLogger(__name__)


class S3Service:
    """
    Service class for handling AWS S3 operations including file uploads, 
    deletions, and CloudFront URL generation.
    
    Attributes:
        s3_client: Boto3 S3 client instance
        bucket_name: Name of the S3 bucket
        cloudfront_domain: CloudFront distribution domain (optional)
    """
    
    ALLOWED_MIME_TYPES = {
        # Images
        'image/jpeg',
        'image/jpg',
        'image/png',
        'image/gif',
        'image/webp',
        'image/svg+xml',
        # Videos
        'video/mp4',
        'video/mpeg',
        'video/quicktime',
        'video/x-msvideo',
        'video/x-ms-wmv',
        'video/webm',
        # Documents
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
        'application/msword',  # .doc
        'text/plain'
    }
    
    def __init__(
        self,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_region: Optional[str] = None,
        bucket_name: Optional[str] = None,
        cloudfront_domain: Optional[str] = None
    ):
        """
        Initialize S3Service with AWS credentials and configuration.
        
        Args:
            aws_access_key_id: AWS access key ID (defaults to env var AWS_ACCESS_KEY_ID)
            aws_secret_access_key: AWS secret access key (defaults to env var AWS_SECRET_ACCESS_KEY)
            aws_region: AWS region (defaults to env var AWS_REGION)
            bucket_name: S3 bucket name (defaults to env var AWS_S3_BUCKET_NAME)
            cloudfront_domain: CloudFront domain (defaults to env var AWS_CLOUDFRONT_DOMAIN)
        """
        self.aws_region = aws_region
        self.bucket_name = bucket_name
        self.cloudfront_domain = cloudfront_domain
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        
        # Configure S3 client
        config = Config(
            region_name=self.aws_region,
            signature_version='s3v4',
            retries={'max_attempts': 3, 'mode': 'standard'}
        )
        
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            config=config
        )
    
    def upload_file(
        self,
        file: Union[bytes, BinaryIO],
        file_name: str,
        folder_path: str,
        mime_type: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Upload file to S3 bucket.
        
        Args:
            file: File content as bytes or file-like object
            file_name: Original filename
            folder_path: Folder path in S3 (e.g., 'announcements', 'documents/user-docs')
            mime_type: File MIME type
            metadata: Optional metadata to attach to the S3 object
            
        Returns:
            Dictionary containing upload result with keys:
                - success (bool): Upload success status
                - url (str): CloudFront or S3 URL
                - key (str): S3 object key
                - bucket (str): S3 bucket name
                - file_name (str): Generated unique filename
                - original_name (str): Original filename
                - etag (str): S3 ETag
                - message (str): Error message if unsuccessful
                
        Raises:
            ValueError: If file type is not allowed
        """
        try:
            if not self.is_valid_file_type(mime_type):
                raise ValueError(
                    'Invalid file type. Allowed types: images (jpeg, jpg, png, gif, webp, svg), '
                    'videos (mp4, mpeg, quicktime, avi, wmv, webm), documents (pdf, docx, doc, txt).'
                )
            
            # Generate unique filename
            file_extension = Path(file_name).suffix
            unique_file_name = f"{uuid.uuid4()}{file_extension}"
            
            # Construct S3 key with folder path
            s3_key = f"{folder_path.rstrip('/')}/{unique_file_name}"
            
            # Prepare upload arguments
            upload_args = {
                'Bucket': self.bucket_name,
                'Key': s3_key,
                'Body': file if isinstance(file, bytes) else file.read(),
                'ContentType': mime_type,
            }
            
            # Add metadata if provided
            if metadata:
                upload_args['Metadata'] = metadata
            
            # Upload to S3
            response = self.s3_client.put_object(**upload_args)
            
            # Get URL (CloudFront or S3)
            url = self.get_cloudfront_url(s3_key)
            
            return {
                'success': True,
                'url': url,
                'key': s3_key,
                'bucket': self.bucket_name,
                'file_name': unique_file_name,
                'original_name': file_name,
                'etag': response.get('ETag', '').strip('"')
            }
            
        except (ClientError, ValueError) as error:
            logger.error(f'S3 upload error: {error}')
            return {
                'success': False,
                'message': str(error)
            }
    
    def get_cloudfront_url(self, s3_key: str) -> str:
        """
        Get CloudFront URL for a given S3 key.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            CloudFront URL if configured, otherwise S3 URL
        """
        if not self.cloudfront_domain:
            # Fallback to S3 URL
            return f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{s3_key}"
        
        # Remove protocol if it exists in the domain
        domain = self.cloudfront_domain.replace('https://', '').replace('http://', '')
        return f"https://{domain}/{s3_key}"
    
    def upload_from_fastapi(
        self,
        upload_file,
        folder_path: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Upload file from FastAPI UploadFile object.
        
        Args:
            upload_file: FastAPI UploadFile object
            folder_path: Folder path in S3
            metadata: Optional metadata to attach to the S3 object
            
        Returns:
            Dictionary containing upload result
            
        Raises:
            ValueError: If no file is provided
        """
        if not upload_file:
            raise ValueError('No file provided')
        
        file_content = upload_file.file.read()
        
        return self.upload_file(
            file=file_content,
            file_name=upload_file.filename,
            folder_path=folder_path,
            mime_type=upload_file.content_type,
            metadata=metadata
        )
    
    def delete_file(self, file_key: str) -> Dict[str, Any]:
        """
        Delete file from S3 bucket.
        
        Args:
            file_key: S3 object key
            
        Returns:
            Dictionary containing deletion result with keys:
                - success (bool): Deletion success status
                - message (str): Success or error message
                - key (str): S3 object key
                
        Raises:
            Exception: If deletion fails
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            
            return {
                'success': True,
                'message': 'File deleted successfully',
                'key': file_key
            }
            
        except ClientError as error:
            raise Exception(f"Failed to delete file from S3: {error}")
    
    def get_signed_url(self, file_key: str, expires_in: int = 3600) -> str:
        """
        Generate a presigned URL for private file access.
        
        Args:
            file_key: S3 object key
            expires_in: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Presigned URL string
            
        Raises:
            Exception: If URL generation fails
        """
        try:
            signed_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_key
                },
                ExpiresIn=expires_in
            )
            
            return signed_url
            
        except ClientError as error:
            raise Exception(f"Failed to generate signed URL: {error}")
    
    def is_valid_file_type(self, mime_type: str) -> bool:
        """
        Validate if the file type is allowed.
        
        Args:
            mime_type: File MIME type
            
        Returns:
            True if file type is allowed, False otherwise
        """
        return mime_type in self.ALLOWED_MIME_TYPES
    
    def file_exists(self, file_key: str) -> bool:
        """
        Check if a file exists in S3.
        
        Args:
            file_key: S3 object key
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=file_key)
            return True
        except ClientError:
            return False
    
    def get_file_metadata(self, file_key: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a file in S3.
        
        Args:
            file_key: S3 object key
            
        Returns:
            Dictionary containing file metadata or None if file doesn't exist
        """
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            
            return {
                'content_type': response.get('ContentType'),
                'content_length': response.get('ContentLength'),
                'last_modified': response.get('LastModified'),
                'etag': response.get('ETag', '').strip('"'),
                'metadata': response.get('Metadata', {})
            }
            
        except ClientError as error:
            return None
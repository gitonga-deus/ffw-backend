import httpx
import hmac
import hashlib
import time
from typing import Optional, Dict, Any
from urllib.parse import urlencode, urlparse, parse_qs
from app.config import settings
from app.utils.file_validation import FileValidator


class StorageService:
    """Service for handling file storage with Vercel Blob."""
    
    def __init__(self):
        self.token = settings.vercel_blob_token
        self.base_url = "https://blob.vercel-storage.com"
        self.max_image_size = settings.max_image_size
        self.max_pdf_size = settings.max_pdf_size
    
    async def upload_file(
        self,
        file_data: bytes,
        filename: str,
        content_type: str = "application/octet-stream",
        validate_size: bool = True,
        max_size: Optional[int] = None
    ) -> Optional[str]:
        """
        Upload a file to Vercel Blob storage with validation.
        
        Args:
            file_data: The file content as bytes
            filename: The name of the file
            content_type: MIME type of the file
            validate_size: Whether to validate file size
            max_size: Maximum file size in bytes (uses defaults if None)
            
        Returns:
            URL of the uploaded file or None if upload fails
        """
        if not self.token:
            print(f"Vercel Blob token not configured. File upload skipped: {filename}")
            return None
        
        # Validate filename
        filename = FileValidator.validate_filename(filename)
        
        # Validate file size
        if validate_size:
            if max_size is None:
                # Determine max size based on content type
                if content_type.startswith('image/'):
                    max_size = self.max_image_size
                elif content_type == 'application/pdf':
                    max_size = self.max_pdf_size
                else:
                    max_size = self.max_pdf_size  # Default to PDF size
            
            if len(file_data) > max_size:
                print(f"File size {len(file_data)} exceeds limit {max_size}")
                return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.base_url}/{filename}",
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Content-Type": content_type,
                        "x-content-type": content_type
                    },
                    content=file_data,
                    timeout=30.0
                )
                response.raise_for_status()
                
                result = response.json()
                return result.get("url")
                
        except Exception as e:
            print(f"Failed to upload file to Vercel Blob: {str(e)}")
            return None
    
    async def upload_image(
        self,
        file_data: bytes,
        filename: str,
        content_type: str = "image/jpeg"
    ) -> Optional[str]:
        """
        Upload an image file to Vercel Blob storage.
        
        Args:
            file_data: The image content as bytes
            filename: The name of the file
            content_type: MIME type of the image
            
        Returns:
            URL of the uploaded image or None if upload fails
        """
        return await self.upload_file(
            file_data=file_data,
            filename=filename,
            content_type=content_type,
            max_size=self.max_image_size
        )
    
    async def upload_pdf(
        self,
        file_data: bytes,
        filename: str
    ) -> Optional[str]:
        """
        Upload a PDF file to Vercel Blob storage.
        
        Args:
            file_data: The PDF content as bytes
            filename: The name of the file
            
        Returns:
            URL of the uploaded PDF or None if upload fails
        """
        return await self.upload_file(
            file_data=file_data,
            filename=filename,
            content_type="application/pdf",
            max_size=self.max_pdf_size
        )
    
    async def delete_file(self, url: str) -> bool:
        """
        Delete a file from Vercel Blob storage.
        
        Args:
            url: The URL of the file to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        if not self.token:
            print(f"Vercel Blob token not configured. File deletion skipped: {url}")
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    url,
                    headers={
                        "Authorization": f"Bearer {self.token}"
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                return True
                
        except Exception as e:
            print(f"Failed to delete file from Vercel Blob: {str(e)}")
            return False
    
    def get_signed_url(
        self,
        url: str,
        expires_in: int = 3600,
        content_disposition: Optional[str] = None
    ) -> str:
        """
        Generate a signed URL for accessing private content.
        
        This implementation creates a time-limited signed URL using HMAC.
        The signature is verified on the backend when serving the content.
        
        Args:
            url: The URL of the file
            expires_in: Expiration time in seconds (default: 1 hour)
            content_disposition: Optional content disposition header (e.g., 'attachment; filename="file.pdf"')
            
        Returns:
            Signed URL with expiration and signature parameters
        """
        if not self.token:
            # If no token configured, return URL as-is (for development)
            return url
        
        # Calculate expiration timestamp
        expires_at = int(time.time()) + expires_in
        
        # Parse the URL to get the path
        parsed_url = urlparse(url)
        path = parsed_url.path
        
        # Create signature payload
        payload = f"{path}:{expires_at}"
        if content_disposition:
            payload += f":{content_disposition}"
        
        # Generate HMAC signature
        signature = hmac.new(
            self.token.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Build query parameters
        params: Dict[str, Any] = {
            'expires': expires_at,
            'signature': signature
        }
        
        if content_disposition:
            params['disposition'] = content_disposition
        
        # Append parameters to URL
        query_string = urlencode(params)
        separator = '&' if parsed_url.query else '?'
        signed_url = f"{url}{separator}{query_string}"
        
        return signed_url
    
    def verify_signed_url(self, url: str) -> bool:
        """
        Verify a signed URL's signature and expiration.
        
        Args:
            url: The signed URL to verify
            
        Returns:
            True if the signature is valid and not expired, False otherwise
        """
        if not self.token:
            # If no token configured, allow access (for development)
            return True
        
        try:
            # Parse URL
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            
            # Extract parameters
            expires_at = int(query_params.get('expires', [0])[0])
            signature = query_params.get('signature', [''])[0]
            content_disposition = query_params.get('disposition', [None])[0]
            
            # Check expiration
            if time.time() > expires_at:
                return False
            
            # Recreate payload
            path = parsed_url.path
            payload = f"{path}:{expires_at}"
            if content_disposition:
                payload += f":{content_disposition}"
            
            # Verify signature
            expected_signature = hmac.new(
                self.token.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            print(f"Failed to verify signed URL: {str(e)}")
            return False
    
    def get_download_url(self, url: str, filename: str, expires_in: int = 3600) -> str:
        """
        Generate a signed URL for downloading a file with a specific filename.
        
        Args:
            url: The URL of the file
            filename: The filename to use for download
            expires_in: Expiration time in seconds (default: 1 hour)
            
        Returns:
            Signed URL with download disposition
        """
        content_disposition = f'attachment; filename="{filename}"'
        return self.get_signed_url(url, expires_in, content_disposition)


# Singleton instance
storage_service = StorageService()

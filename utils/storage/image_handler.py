"""
Image handler for the class report application.
"""
import os
import mimetypes
from typing import Optional
from utils.common.logging_utils import get_logger

logger = get_logger(__name__)

class ImageHandler:
    """
    Handler for image operations.
    """
    
    def __init__(self, storage_service=None):
        """
        Initialize the image handler.
        
        Args:
            storage_service: The storage service to use for uploading images
        """
        self.storage_service = storage_service
    
    def get_mime_type(self, file_name: str) -> str:
        """
        Get the MIME type of a file.
        
        Args:
            file_name: The name of the file
            
        Returns:
            The MIME type of the file
        """
        # Initialize mimetypes
        if not mimetypes.inited:
            mimetypes.init()
        
        # Get the MIME type based on the file extension
        mime_type, _ = mimetypes.guess_type(file_name)
        
        # Default to application/octet-stream if the MIME type cannot be determined
        if mime_type is None:
            mime_type = "application/octet-stream"
        
        return mime_type
    
    def upload_image(self, image_path: str) -> Optional[str]:
        """
        Upload an image to the storage service.
        
        Args:
            image_path: The path to the image
            
        Returns:
            The URL of the uploaded image, or None if the upload failed
        """
        logger.info(f"Uploading image: {image_path}")
        
        try:
            # Check if the file exists
            if not os.path.exists(image_path):
                logger.error(f"Image file not found: {image_path}")
                return None
            
            # Check if the storage service is available
            if self.storage_service:
                # Upload the image
                image_url = self.storage_service.upload_image(image_path)
                if image_url:
                    logger.info(f"Image uploaded: {image_url}")
                    return image_url
                else:
                    logger.warning(f"Failed to upload image, returning local path as fallback")
                    # Return the local path as a fallback
                    return f"file://{image_path}"
            else:
                logger.warning("Storage service is not available, returning local path as fallback")
                # Return the local path as a fallback
                return f"file://{image_path}"
        
        except Exception as e:
            logger.error(f"Error uploading image: {str(e)}")
            # Return the local path as a fallback
            return f"file://{image_path}" 
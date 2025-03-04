import os
import logging
import uuid
from google.cloud import storage
from google.oauth2 import service_account

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self, credentials_json=None):
        """
        Initialize the Google Cloud Storage client.
        
        Args:
            credentials_json: Path to the service account JSON file.
                              If None, will use Application Default Credentials (ADC).
                              This parameter is kept for backward compatibility but is ignored.
        """
        logger.info("Initializing Storage Service")
        
        try:
            # Step 1: Validate bucket name
            self._validate_bucket_name()
            
            # Step 2: Setup client using ADC
            self._setup_client()
            
            # Log successful initialization
            logger.info(f"Using GCS bucket: {self.bucket_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {str(e)}")
            raise
    
    def _validate_bucket_name(self):
        """Validate that the GCS bucket name is set in environment variables."""
        self.bucket_name = os.getenv("GCS_BUCKET_NAME")
        if not self.bucket_name:
            logger.warning("GCS_BUCKET_NAME environment variable not set")
            raise ValueError("GCS_BUCKET_NAME environment variable is required")
    
    def _setup_client(self):
        """Setup GCS client using Application Default Credentials (ADC)."""
        try:
            # Use Application Default Credentials (ADC)
            # This will automatically use gcloud CLI credentials or metadata server on GCE
            self.client = storage.Client()
            logger.info("GCS client initialized with Application Default Credentials (ADC)")
        except Exception as e:
            logger.error(f"Failed to initialize GCS client with ADC: {str(e)}")
            raise ValueError(f"Failed to initialize with Application Default Credentials: {str(e)}")
    
    def upload_image(self, image_path, folder="sunday_school_reports"):
        """
        Upload an image to Google Cloud Storage and return its public URL.
        
        Args:
            image_path: Path to the local image file
            folder: Folder in the bucket to store the image (default: sunday_school_reports)
            
        Returns:
            Public URL of the uploaded image
        """
        logger.info(f"Uploading image to GCS: {image_path}")
        
        try:
            # Check if file exists
            if not os.path.exists(image_path):
                logger.error(f"Image file not found: {image_path}")
                return None
                
            # Generate a unique blob name to avoid collisions
            file_extension = os.path.splitext(image_path)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            blob_name = f"{folder}/{unique_filename}"
            
            # Get bucket and create blob
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(blob_name)
            
            # Upload file
            blob.upload_from_filename(image_path)
            logger.info(f"Image uploaded to GCS: gs://{self.bucket_name}/{blob_name}")
            
            # Get URL (no need to make public as permissions are controlled by IAM)
            # Format: https://storage.googleapis.com/BUCKET_NAME/OBJECT_NAME
            public_url = f"https://storage.googleapis.com/{self.bucket_name}/{blob_name}"
            logger.info(f"GCS URL: {public_url}")
            
            return public_url
            
        except Exception as e:
            logger.error(f"Error uploading image to GCS: {str(e)}")
            return None

    def generate_signed_url(self, file_extension, folder="sunday_school_reports", content_type=None, expires_after_minutes=15):
        """
        生成一個簽名 URL，用於直接從瀏覽器上傳圖片到 GCS
        
        Args:
            file_extension: 文件擴展名（例如：.jpg, .png）
            folder: GCS 中的文件夾路徑
            content_type: 文件的 MIME 類型
            expires_after_minutes: URL 有效期（分鐘）
            
        Returns:
            dict: 包含簽名 URL 和 blob 名稱的字典
        """
        logger.info(f"Generating signed URL for direct upload with extension: {file_extension}")
        
        try:
            # 根據文件擴展名確定內容類型
            if not content_type:
                content_types = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.gif': 'image/gif',
                    '.webp': 'image/webp',
                    '.bmp': 'image/bmp',
                    '.tiff': 'image/tiff',
                    '.tif': 'image/tiff'
                }
                content_type = content_types.get(file_extension.lower(), 'application/octet-stream')
            
            # 生成唯一的 blob 名稱
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            blob_name = f"{folder}/{unique_filename}"
            
            # 獲取 bucket 和創建 blob
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(blob_name)
            
            # 生成簽名 URL，設置為 PUT 方法以允許上傳
            url = blob.generate_signed_url(
                version="v4",
                expiration=expires_after_minutes * 60,  # 轉換為秒
                method="PUT",
                content_type=content_type,
            )
            
            logger.info(f"Generated signed URL for blob: {blob_name}")
            
            return {
                "signed_url": url,
                "blob_name": blob_name,
                "public_url": f"https://storage.googleapis.com/{self.bucket_name}/{blob_name}"
            }
            
        except Exception as e:
            logger.error(f"Error generating signed URL: {str(e)}")
            return None

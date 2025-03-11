import os
import logging
import uuid
from google.cloud import storage
from google.oauth2 import service_account

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Storage paths configuration
IMAGES_FOLDER = "images"
HTML_FOLDER = "reports"
DEFAULT_FOLDER = "sunday_school_reports"

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
    
    def _get_storage_path(self, base_folder: str, sub_folder: str = None) -> str:
        """
        Generate storage path by combining base folder and sub folder
        
        Args:
            base_folder: Base folder name (e.g., DEFAULT_FOLDER)
            sub_folder: Sub folder name (e.g., IMAGES_FOLDER or HTML_FOLDER)
            
        Returns:
            Combined storage path
        """
        if sub_folder:
            return f"{base_folder}/{sub_folder}"
        return base_folder
    
    def upload_image(self, image_path, folder=DEFAULT_FOLDER):
        """
        Upload an image to Google Cloud Storage and return its public URL.
        
        Args:
            image_path: Path to the local image file
            folder: Base folder in the bucket (default: sunday_school_reports)
            
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
            storage_path = self._get_storage_path(folder, IMAGES_FOLDER)
            blob_name = f"{storage_path}/{unique_filename}"
            
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

    def upload_html(self, html_content: str, filename: str, folder=DEFAULT_FOLDER) -> str:
        """
        Upload HTML content to Google Cloud Storage and return its public URL.
        
        Args:
            html_content: HTML content as string
            filename: Name of the file (without extension)
            folder: Base folder in the bucket (default: sunday_school_reports)
            
        Returns:
            Public URL of the uploaded HTML file
        """
        logger.info(f"Uploading HTML content to GCS: {filename}")
        
        try:
            # Generate blob name with HTML folder
            storage_path = self._get_storage_path(folder, HTML_FOLDER)
            blob_name = f"{storage_path}/{filename}.html"
            
            # Get bucket and create blob
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(blob_name)
            
            # Upload content with explicit content type
            blob.upload_from_string(
                data=html_content,
                content_type='text/html',
                num_retries=3
            )
            logger.info(f"HTML uploaded to GCS: gs://{self.bucket_name}/{blob_name}")
            
            # Get URL
            public_url = f"https://storage.googleapis.com/{self.bucket_name}/{blob_name}"
            logger.info(f"GCS URL: {public_url}")
            
            return public_url
            
        except Exception as e:
            logger.error(f"Error uploading HTML to GCS: {str(e)}")
            return None

    def list_reports(self, folder=DEFAULT_FOLDER) -> list:
        """
        List all HTML files in the specified folder in Google Cloud Storage and return their properties.
        
        Args:
            folder: Base folder in the bucket (default: sunday_school_reports)
            
        Returns:
            List of dictionaries containing properties of HTML files
        """
        logger.info(f"Listing reports in GCS folder: {folder}/{HTML_FOLDER}")
        
        try:
            # Get bucket
            bucket = self.client.bucket(self.bucket_name)
            # Create a prefix for the HTML folder
            prefix = self._get_storage_path(folder, HTML_FOLDER) + "/"
            blobs = bucket.list_blobs(prefix=prefix)
            
            # Collect properties of HTML files
            html_files = [
                {
                    "name": os.path.basename(blob.name),
                    "url": f"https://storage.googleapis.com/{self.bucket_name}/{blob.name}",
                    "date": blob.updated
                }
                for blob in blobs if blob.name.endswith('.html')
            ]
            
            # Sort the list of files by date (newest first)
            html_files.sort(key=lambda x: x['date'], reverse=True)
            
            logger.info(f"Found HTML files: {html_files}")
            
            return html_files
            
        except Exception as e:
            logger.error(f"Error listing reports in GCS: {str(e)}")
            return []

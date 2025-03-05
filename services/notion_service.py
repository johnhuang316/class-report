import os
import json
import logging
from typing import Dict, List, Any, Optional
import requests
from services.storage_service import StorageService
from utils.notion.api_wrapper import NotionApiClient
from utils.notion.block_builder import NotionBlockBuilder
from utils.markdown.parser import MarkdownParser
from utils.storage.image_handler import ImageHandler
from utils.common.logging_utils import get_logger

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = get_logger(__name__)

class NotionService:
    def __init__(self, api_key: str):
        """Initialize the Notion client with the API key."""
        logger.info("Initializing NotionService")
        if not api_key:
            logger.error("API key is empty or None")
            raise ValueError("Notion API key is required")
        
        # Initialize API client
        self.api_client = NotionApiClient(api_key)
        
        # Initialize block builder
        self.block_builder = NotionBlockBuilder()
        
        # Initialize markdown parser
        self.markdown_parser = MarkdownParser()
        
        # Initialize Storage service
        try:
            self.storage_service = StorageService()
            logger.info("Storage service initialized successfully")
            
            # Initialize image handler with storage service
            self.image_handler = ImageHandler(self.storage_service)
            logger.info("Image handler initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Storage service: {str(e)}")
            self.storage_service = None
            
            # Initialize image handler without storage service
            self.image_handler = ImageHandler()
            logger.info("Image handler initialized without storage service")
        
        logger.info("NotionService initialized successfully")
    
    def get_page_content(self, page_id: str) -> Dict[str, Any]:
        """
        Extract content from a Notion page including text and images.
        
        Args:
            page_id: The ID of the Notion page
            
        Returns:
            A dictionary containing the extracted text and image URLs
        """
        logger.info(f"Getting content from page: {page_id}")
        
        try:
            # Get the page
            page_data = self.api_client.get_page(page_id)
            
            # Get the blocks
            blocks = self.api_client.get_page_blocks(page_id)
            
            # Extract content using block builder
            return self.block_builder.extract_content(page_data, blocks)
            
        except Exception as e:
            logger.error(f"Error getting page content: {str(e)}")
            raise

    def create_page(self, title: str, content: list, image_paths: list = None, report_date: str = None):
        """
        Create a new Notion page for Sunday School report
        
        Args:
            title: Report title
            content: List of report content paragraphs
            image_paths: List of photo paths
            report_date: Report date in YYYY-MM-DD format (optional)
            
        Returns:
            (page_url, page_id)
        """
        logger.info(f"Creating Notion page with title: {title}")
        logger.info(f"Content length: {len(content)} paragraphs")
        logger.info(f"Number of images: {len(image_paths) if image_paths else 0}")
        logger.info(f"Report date: {report_date}")
        
        # Format the report date using block builder
        formatted_date = self.block_builder.format_date(report_date)
        
        # Prepare the page content
        report_content = {
            "title": title,
            "content": content,
            "image_paths": image_paths,
            "report_date": formatted_date
        }
        
        # Create the page
        try:
            page_id = self.create_report_page(report_content)
            page_url = f"https://notion.so/{page_id.replace('-', '')}"
            logger.info(f"Created Notion page: {page_url}")
            return page_url, page_id
        except Exception as e:
            logger.error(f"Failed to create Notion page: {str(e)}")
            raise
    
    def create_report_page(self, report_content: Dict[str, Any]):
        """
        Create a new Notion page with the generated report.
        
        Args:
            report_content: Dictionary containing the report title, content, and images
            
        Returns:
            The ID of the newly created page
        """
        logger.info("Creating report page in Notion")
        
        # Get the database ID from environment variable
        database_id = os.environ.get("NOTION_DATABASE_ID")
        if not database_id:
            logger.error("NOTION_DATABASE_ID environment variable is not set")
            raise ValueError("NOTION_DATABASE_ID environment variable is required")
        
        # Process images if provided
        if "image_paths" in report_content and report_content["image_paths"]:
            processed_image_paths = []
            for image_path in report_content["image_paths"]:
                if image_path:
                    # Upload image to storage service
                    image_url = self.upload_image_to_notion(image_path)
                    processed_image_paths.append(image_url)
            
            # Update the report content with the processed image paths
            report_content["image_paths"] = processed_image_paths
        
        # Build the blocks for the page
        blocks = self.block_builder.build_page_blocks(report_content)
        
        # Create the page
        return self.api_client.create_page(database_id, report_content["title"], blocks)
    
    def set_page_public_permissions(self, page_id: str) -> bool:
        """
        Attempt to set page permissions to be visible to all workspace members
        
        Note: Notion API currently does not support modifying page permissions.
        This method only adds log warnings. Page permissions need to be set manually
        in the Notion web interface.
        
        Args:
            page_id: Notion page ID
            
        Returns:
            Always returns False, as the API does not support this feature
        """
        logger.warning("Notion API does not support setting page permissions automatically")
        logger.warning("Please set the page to 'Visible to everyone in the workspace' manually in Notion")
        return False
    
    def upload_image_to_notion(self, image_path: str) -> str:
        """
        上傳圖片到 GCS 並返回圖片的外部 URL
        
        Args:
            image_path: 圖片的本地路徑
            
        Returns:
            圖片的外部 URL
            
        Note:
            圖片會上傳到 GCS，本地臨時文件會在上傳後刪除
        """
        logger.info(f"Uploading image to GCS: {image_path}")
        
        # Use image handler to upload the image
        return self.image_handler.upload_image(image_path)

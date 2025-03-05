"""
Notion API wrapper for the class report application.
"""
import os
import requests
from typing import Dict, List, Any, Optional
from utils.common.logging_utils import get_logger

logger = get_logger(__name__)

class NotionApiClient:
    """
    Wrapper for the Notion API.
    """
    def __init__(self, api_key: str):
        """
        Initialize the Notion API client.
        
        Args:
            api_key: The Notion API key
        """
        if not api_key:
            logger.error("API key is empty or None")
            raise ValueError("Notion API key is required")
        
        # Log a masked version of the API key for debugging
        masked_key = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "***"
        logger.info(f"Using Notion API key: {masked_key}")
        
        self.api_key = api_key
        self.base_url = "https://api.notion.com/v1"
        
        # Handle API key format
        auth_value = f"Bearer {api_key}"
            
        self.headers = {
            "Authorization": auth_value,
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        logger.info("Notion API client initialized successfully")
    
    def get_page(self, page_id: str) -> Dict[str, Any]:
        """
        Get a page from Notion.
        
        Args:
            page_id: The ID of the page
            
        Returns:
            The page data
        """
        logger.info(f"Getting page: {page_id}")
        
        response = requests.get(
            f"{self.base_url}/pages/{page_id}",
            headers=self.headers
        )
        response.raise_for_status()
        
        return response.json()
    
    def get_page_blocks(self, page_id: str) -> List[Dict[str, Any]]:
        """
        Get the blocks of a page.
        
        Args:
            page_id: The ID of the page
            
        Returns:
            The blocks of the page
        """
        logger.info(f"Getting blocks for page: {page_id}")
        
        response = requests.get(
            f"{self.base_url}/blocks/{page_id}/children",
            headers=self.headers
        )
        response.raise_for_status()
        
        return response.json()["results"]
    
    def create_page(self, database_id: str, title: str, blocks: List[Dict[str, Any]]) -> str:
        """
        Create a new page in a database.
        
        Args:
            database_id: The ID of the database
            title: The title of the page
            blocks: The blocks of the page
            
        Returns:
            The ID of the newly created page
        """
        logger.info(f"Creating page in database: {database_id}")
        
        # Prepare the request body
        data = {
            "parent": {"database_id": database_id},
            "properties": {
                "title": {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                }
            },
            "children": blocks
        }
        
        # Create the page
        response = requests.post(
            f"{self.base_url}/pages",
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        
        page_id = response.json()["id"]
        logger.info(f"Created page: {page_id}")
        
        return page_id
    
    def append_blocks(self, block_id: str, blocks: List[Dict[str, Any]]) -> bool:
        """
        Append blocks to a block.
        
        Args:
            block_id: The ID of the block
            blocks: The blocks to append
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Appending blocks to block: {block_id}")
        
        try:
            response = requests.patch(
                f"{self.base_url}/blocks/{block_id}/children",
                headers=self.headers,
                json={"children": blocks}
            )
            response.raise_for_status()
            
            return True
        except Exception as e:
            logger.error(f"Error appending blocks: {str(e)}")
            return False 
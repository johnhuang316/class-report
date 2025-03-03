import os
import requests
from typing import Dict, List, Any, Optional
from notion_client import Client

class NotionClient:
    def __init__(self, api_key: str):
        """Initialize the Notion client with the API key."""
        self.client = Client(auth=api_key)
    
    def get_page_content(self, page_id: str) -> Dict[str, Any]:
        """
        Extract content from a Notion page including text and images.
        
        Args:
            page_id: The ID of the Notion page
            
        Returns:
            A dictionary containing the extracted text and image URLs
        """
        # Get the page properties
        page = self.client.pages.retrieve(page_id=page_id)
        
        # Get the page blocks (content)
        blocks = self.client.blocks.children.list(block_id=page_id)
        
        # Extract text content and image URLs
        text_content = []
        image_urls = []
        
        for block in blocks.get("results", []):
            block_type = block.get("type")
            
            # Extract text from various block types
            if block_type in ["paragraph", "heading_1", "heading_2", "heading_3", "bulleted_list_item", "numbered_list_item"]:
                rich_text = block.get(block_type, {}).get("rich_text", [])
                if rich_text:
                    text_content.append("".join([rt.get("plain_text", "") for rt in rich_text]))
            
            # Extract image URLs
            elif block_type == "image":
                image_block = block.get("image", {})
                if "file" in image_block:
                    image_urls.append(image_block["file"]["url"])
                elif "external" in image_block:
                    image_urls.append(image_block["external"]["url"])
        
        # Get page title if available
        title = ""
        if "properties" in page and "title" in page["properties"]:
            title_property = page["properties"]["title"]
            if "title" in title_property and title_property["title"]:
                title = "".join([t.get("plain_text", "") for t in title_property["title"]])
        
        return {
            "title": title,
            "text_content": text_content,
            "image_urls": image_urls
        }
    
    def create_report_page(self, report_content: Dict[str, Any]) -> str:
        """
        Create a new Notion page with the generated report.
        
        Args:
            report_content: Dictionary containing the report title, content, and images
            
        Returns:
            The ID of the newly created page
        """
        # Get the parent database ID from environment variable
        parent_database_id = os.getenv("NOTION_DATABASE_ID")
        if not parent_database_id:
            raise ValueError("NOTION_DATABASE_ID environment variable is not set")
        
        # Create the page
        new_page = self.client.pages.create(
            parent={"database_id": parent_database_id},
            properties={
                "title": {
                    "title": [
                        {
                            "text": {
                                "content": report_content["title"]
                            }
                        }
                    ]
                }
            }
        )
        
        page_id = new_page["id"]
        
        # Add content blocks to the page
        blocks = []
        
        # Add text content
        for paragraph in report_content["content"]:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": paragraph
                            }
                        }
                    ]
                }
            })
        
        # Add images
        for image_url in report_content["image_urls"]:
            blocks.append({
                "object": "block",
                "type": "image",
                "image": {
                    "type": "external",
                    "external": {
                        "url": image_url
                    }
                }
            })
        
        # Add blocks to the page
        self.client.blocks.children.append(
            block_id=page_id,
            children=blocks
        )
        
        return page_id

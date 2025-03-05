"""
Notion block builder for the class report application.
"""
from typing import Dict, List, Any, Optional
from utils.common.logging_utils import get_logger

logger = get_logger(__name__)

class NotionBlockBuilder:
    """
    Builder for Notion blocks.
    """
    
    def build_page_blocks(self, report_content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Build blocks for a Notion page.
        
        Args:
            report_content: Dictionary containing the report content
            
        Returns:
            List of Notion blocks
        """
        blocks = []
        
        # Add title with callout block for better visual appeal
        if "title" in report_content and report_content["title"]:
            blocks.append(self._create_title_block(report_content["title"]))
        
        # Add date with better formatting
        if "report_date" in report_content and report_content["report_date"]:
            report_date = report_content["report_date"]
            blocks.append(self._create_date_block(report_date))
        
        # Add a decorative divider
        blocks.append(self._create_divider_block())
        
        # Add a welcome callout block
        blocks.append({
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "歡迎閱讀本週主日學報告！以下是本週的活動摘要和精彩時刻。"
                        }
                    }
                ],
                "icon": {
                    "type": "emoji",
                    "emoji": "📝"
                },
                "color": "blue_background"
            }
        })
        
        # Process content with better section formatting
        if "content" in report_content and report_content["content"]:
            logger.info(f"Processing content: {report_content['content']}") 
            from utils.markdown.parser import MarkdownParser
            markdown_parser = MarkdownParser()
            content_blocks = markdown_parser.process_content(report_content["content"])
            blocks.extend(content_blocks)
        
        # Add images with better gallery-like formatting
        if "image_paths" in report_content and report_content["image_paths"]:
            # Add a divider before images
            blocks.append(self._create_divider_block())
            
            # Add a heading for the images section with emoji
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "📸 活動照片集錦"
                            }
                        }
                    ],
                    "color": "blue_background"
                }
            })
            
            # Add a brief intro to the photos
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "以下是本週活動的精彩瞬間："
                            },
                            "annotations": {
                                "italic": True
                            }
                        }
                    ]
                }
            })
            
            # Add images
            for image_url in report_content["image_paths"]:
                if image_url:
                    blocks.append(self._create_image_block(image_url))
        
        # Add a footer section
        blocks.append(self._create_divider_block())
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "感謝您閱讀本週報告！下週再見！"
                        },
                        "annotations": {
                            "italic": True,
                            "color": "gray"
                        }
                    }
                ],
                "color": "default"
            }
        })
        
        return blocks
    
    def extract_content(self, page_data: Dict[str, Any], blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract content from a Notion page.
        
        Args:
            page_data: The page data
            blocks: The blocks of the page
            
        Returns:
            Dictionary containing the extracted content
        """
        # Extract text and images
        content = []
        images = []
        
        for block in blocks:
            if block["type"] == "paragraph":
                # Extract text from paragraph blocks
                text = ""
                for rich_text in block["paragraph"]["rich_text"]:
                    if rich_text["type"] == "text":
                        text += rich_text["text"]["content"]
                if text:
                    content.append(text)
            
            elif block["type"] == "image":
                # Extract image URLs
                if block["image"]["type"] == "external":
                    images.append(block["image"]["external"]["url"])
                elif block["image"]["type"] == "file":
                    images.append(block["image"]["file"]["url"])
        
        return {
            "title": page_data["properties"]["title"]["title"][0]["text"]["content"] if "title" in page_data["properties"] else "",
            "content": content,
            "images": images
        }
    
    def format_date(self, date_str: str) -> str:
        """
        Format a date string in Chinese format.
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            Formatted date string in Chinese format
        """
        if not date_str:
            return ""
        
        try:
            # Parse the date from YYYY-MM-DD format
            year, month, day = date_str.split('-')
            # Format as Chinese date
            formatted_date = f"{year}年{month}月{day}日"
            logger.info(f"Formatted date: {formatted_date}")
            return formatted_date
        except Exception as e:
            logger.warning(f"Failed to parse date {date_str}: {str(e)}")
            return date_str  # Use as-is if parsing fails
    
    def _create_title_block(self, title: str) -> Dict[str, Any]:
        """
        Create a title block.
        
        Args:
            title: The title text
            
        Returns:
            A Notion heading block
        """
        return {
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": title
                        },
                        "annotations": {
                            "bold": True,
                            "color": "blue"
                        }
                    }
                ],
                "color": "default"
            }
        }
    
    def _create_date_block(self, date: str) -> Dict[str, Any]:
        """
        Create a date block.
        
        Args:
            date: The date text
            
        Returns:
            A Notion paragraph block
        """
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": date
                        },
                        "annotations": {
                            "italic": True,
                            "color": "gray"
                        }
                    }
                ]
            }
        }
    
    def _create_divider_block(self) -> Dict[str, Any]:
        """
        Create a divider block.
        
        Returns:
            A Notion divider block
        """
        return {
            "object": "block",
            "type": "divider",
            "divider": {}
        }
    
    def _create_image_block(self, image_url: str) -> Dict[str, Any]:
        """
        Create an image block.
        
        Args:
            image_url: The URL of the image
            
        Returns:
            A Notion image block
        """
        # Determine if the image is external or local
        if image_url.startswith(('http://', 'https://')):
            # Add a caption to the image
            return {
                "object": "block",
                "type": "image",
                "image": {
                    "type": "external",
                    "external": {
                        "url": image_url
                    },
                    "caption": [
                        {
                            "type": "text",
                            "text": {
                                "content": "主日學活動照片"
                            }
                        }
                    ]
                }
            }
        elif image_url.startswith('file://'):
            # This is a local file, but we can't upload it directly
            # In a real application, we would need to upload it first
            logger.warning(f"Local image URL not supported in Notion API: {image_url}")
            return {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": f"[Image: {image_url}]"
                            },
                            "annotations": {
                                "italic": True,
                                "color": "gray"
                            }
                        }
                    ]
                }
            }
        else:
            # Assume it's an external URL
            return {
                "object": "block",
                "type": "image",
                "image": {
                    "type": "external",
                    "external": {
                        "url": image_url
                    },
                    "caption": [
                        {
                            "type": "text",
                            "text": {
                                "content": "主日學活動照片"
                            }
                        }
                    ]
                }
            } 
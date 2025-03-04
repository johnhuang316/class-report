import os
import json
import logging
from typing import Dict, List, Any, Optional
import requests
from services.storage_service import StorageService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NotionService:
    def __init__(self, api_key: str):
        """Initialize the Notion client with the API key."""
        logger.info("Initializing NotionService")
        if not api_key:
            logger.error("API key is empty or None")
            raise ValueError("Notion API key is required")
        
        # Log a masked version of the API key for debugging
        masked_key = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "***"
        logger.info(f"Using Notion API key: {masked_key}")
        
        self.api_key = api_key
        self.base_url = "https://api.notion.com/v1"
        
        # Handle ntn_ format API keys
        auth_value = api_key
        if api_key.startswith("ntn_"):
            # New format API key, use directly
            auth_value = api_key
        else:
            # Old format API key, add Bearer prefix
            auth_value = f"Bearer {api_key}"
            
        self.headers = {
            "Authorization": auth_value,
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        # Initialize Storage service
        try:
            self.storage_service = StorageService()
            logger.info("Storage service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Storage service: {str(e)}")
            self.storage_service = None
        
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
            response = requests.get(
                f"{self.base_url}/pages/{page_id}",
                headers=self.headers
            )
            response.raise_for_status()
            page_data = response.json()
            
            # Get the blocks
            response = requests.get(
                f"{self.base_url}/blocks/{page_id}/children",
                headers=self.headers
            )
            response.raise_for_status()
            blocks = response.json()["results"]
            
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
        
        # Format the report date in Chinese format if provided
        formatted_date = ""
        if report_date:
            try:
                # Parse the date from YYYY-MM-DD format
                year, month, day = report_date.split('-')
                # Format as Chinese date
                formatted_date = f"{year}年{month}月{day}日"
                logger.info(f"Formatted date: {formatted_date}")
            except Exception as e:
                logger.warning(f"Failed to parse date {report_date}: {str(e)}")
                formatted_date = report_date  # Use as-is if parsing fails
        
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
    
    def _parse_markdown_line(self, line: str):
        """
        Parse a single line of markdown and convert to Notion rich text format
        
        Args:
            line: A line of markdown text
            
        Returns:
            List of rich text objects
        """
        rich_text = []
        
        # Process bold text (**text**)
        import re
        
        # Process text with both bold and italic
        bold_italic_pattern = r'\*\*\*(.*?)\*\*\*'
        for match in re.finditer(bold_italic_pattern, line):
            text = match.group(1)
            rich_text.append({
                "type": "text",
                "text": {"content": text},
                "annotations": {
                    "bold": True,
                    "italic": True
                }
            })
            # Replace the matched text to avoid double processing
            line = line.replace(f"***{text}***", " " * len(text))
        
        # Process bold text (**text**)
        bold_pattern = r'\*\*(.*?)\*\*'
        for match in re.finditer(bold_pattern, line):
            text = match.group(1)
            rich_text.append({
                "type": "text",
                "text": {"content": text},
                "annotations": {"bold": True}
            })
            # Replace the matched text to avoid double processing
            line = line.replace(f"**{text}**", " " * len(text))
        
        # Process italic text (*text*)
        italic_pattern = r'\*(.*?)\*'
        for match in re.finditer(italic_pattern, line):
            text = match.group(1)
            rich_text.append({
                "type": "text",
                "text": {"content": text},
                "annotations": {"italic": True}
            })
            # Replace the matched text to avoid double processing
            line = line.replace(f"*{text}*", " " * len(text))
        
        # Add remaining text
        if line.strip():
            rich_text.append({
                "type": "text",
                "text": {"content": line}
            })
        
        return rich_text
    
    def _process_markdown_content(self, content: list):
        """
        Process markdown content and convert to Notion blocks
        
        Args:
            content: List of markdown content lines
            
        Returns:
            List of Notion blocks
        """
        blocks = []
        current_text = ""
        in_quote = False
        in_list = False
        
        for line in content:
            line = line.rstrip()
            
            # Skip empty lines
            if not line:
                if current_text:
                    # Add accumulated text as paragraph
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": self._parse_markdown_line(current_text)
                        }
                    })
                    current_text = ""
                continue
            
            # Process headings
            if line.startswith('# '):
                # Flush any accumulated text
                if current_text:
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": self._parse_markdown_line(current_text)
                        }
                    })
                    current_text = ""
                
                # Add heading
                heading_text = line[2:].strip()
                blocks.append({
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": self._parse_markdown_line(heading_text),
                        "color": "blue_background"
                    }
                })
                continue
            
            # Process subheadings
            elif line.startswith('## '):
                # Flush any accumulated text
                if current_text:
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": self._parse_markdown_line(current_text)
                        }
                    })
                    current_text = ""
                
                # Add subheading
                heading_text = line[3:].strip()
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": self._parse_markdown_line(heading_text),
                        "color": "purple_background"
                    }
                })
                continue
            
            # Process dividers
            elif line.startswith('---'):
                # Flush any accumulated text
                if current_text:
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": self._parse_markdown_line(current_text)
                        }
                    })
                    current_text = ""
                
                # Add divider
                blocks.append({
                    "object": "block",
                    "type": "divider",
                    "divider": {}
                })
                continue
            
            # Process blockquotes
            elif line.startswith('> '):
                # Flush any accumulated text if not in a quote
                if current_text and not in_quote:
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": self._parse_markdown_line(current_text)
                        }
                    })
                    current_text = ""
                
                in_quote = True
                quote_text = line[2:].strip()
                
                # Add quote
                blocks.append({
                    "object": "block",
                    "type": "quote",
                    "quote": {
                        "rich_text": self._parse_markdown_line(quote_text),
                        "color": "gray_background"
                    }
                })
                continue
            else:
                in_quote = False
            
            # Process bullet points
            if line.startswith('• ') or line.startswith('- '):
                # Flush any accumulated text if not in a list
                if current_text and not in_list:
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": self._parse_markdown_line(current_text)
                        }
                    })
                    current_text = ""
                
                in_list = True
                list_text = line[2:].strip()
                
                # Add bullet point
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": self._parse_markdown_line(list_text)
                    }
                })
                continue
            else:
                in_list = False
            
            # Regular paragraph text
            if current_text:
                current_text += "\n" + line
            else:
                current_text = line
        
        # Add any remaining text
        if current_text:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": self._parse_markdown_line(current_text)
                }
            })
        
        return blocks
        
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
        database_id = os.getenv("NOTION_DATABASE_ID")
        if not database_id:
            logger.error("NOTION_DATABASE_ID environment variable is not set")
            raise ValueError("NOTION_DATABASE_ID environment variable is required")
        
        # Create page title with date if available
        page_title = report_content["title"]
        if "report_date" in report_content and report_content["report_date"]:
            page_title = f"{page_title} - {report_content['report_date']}"
        
        # Prepare the request payload
        payload = {
            "parent": {
                "database_id": database_id
            },
            "properties": {
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": page_title
                            }
                        }
                    ]
                }
            },
            "children": []
        }
        
        # Add a cover image if available
        if "cover_image" in report_content and report_content["cover_image"]:
            payload["cover"] = {
                "type": "external",
                "external": {
                    "url": report_content["cover_image"]
                }
            }
        
        # Add a cute emoji icon
        payload["icon"] = {
            "type": "emoji",
            "emoji": "👼"
        }
        
        # Process content
        blocks = []
        
        # Add title with date
        blocks.append({
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": page_title
                        },
                        "annotations": {
                            "bold": True,
                            "color": "blue"
                        }
                    }
                ],
                "color": "blue_background"
            }
        })
        
        # Add date if available
        if "report_date" in report_content and report_content["report_date"]:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": f"📅 日期：{report_content['report_date']}"
                            },
                            "annotations": {
                                "bold": True,
                                "color": "purple"
                            }
                        }
                    ]
                }
            })
        
        # Add a cute divider
        blocks.append({
            "object": "block",
            "type": "divider",
            "divider": {}
        })
        
        # Process content as markdown
        if "content" in report_content and report_content["content"]:
            content_blocks = self._process_markdown_content(report_content["content"])
            blocks.extend(content_blocks)
        
        # Add a divider before images
        blocks.append({
            "object": "block",
            "type": "divider",
            "divider": {}
        })
        
        # Add images if available
        if "image_paths" in report_content and report_content["image_paths"]:
            # Add a cute image grid hint
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "🎠 滑動查看更多精彩照片 🎡"
                            },
                            "annotations": {
                                "bold": True,
                                "italic": True,
                                "color": "blue"
                            }
                        }
                    ]
                }
            })
            
            # Process each image
            cute_emojis = ["🧸", "🎈", "🌈", "🦄", "🎀", "🍭", "🎁", "🌻", "🦋", "🐣"]
            for idx, img_path in enumerate(report_content["image_paths"]):
                try:
                    # Check if the file exists
                    if os.path.exists(img_path):
                        logger.info(f"Uploading image: {img_path}")
                        
                        # Choose a cute emoji
                        cute_emoji = cute_emojis[idx % len(cute_emojis)]
                        
                        # Upload image to GCS
                        image_url = self.upload_image_to_notion(img_path)
                        
                        # If successful, create image block
                        if image_url:
                            blocks.append({
                                "object": "block",
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [
                                        {
                                            "type": "text",
                                            "text": {
                                                "content": f"{cute_emoji} 精彩瞬間 {idx+1} {cute_emoji}"
                                            },
                                            "annotations": {
                                                "bold": True,
                                                "color": "orange"
                                            }
                                        }
                                    ]
                                }
                            })
                            
                            # Add image block (using external URL)
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
                        else:
                            logger.warning(f"Failed to upload image: {img_path}")
                    else:
                        logger.warning(f"Image file not found: {img_path}")
                except Exception as e:
                    logger.error(f"Error processing image {img_path}: {str(e)}")
        
        # Add a cute footer
        blocks.append({
            "object": "block",
            "type": "divider",
            "divider": {}
        })
        
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "💖 感謝您關注我們的主日學活動！💖"
                        },
                        "annotations": {
                            "bold": True,
                            "color": "pink"
                        }
                    }
                ]
            }
        })
        
        # Add blocks to the page in batches (Notion API limit is 100 blocks per request)
        for i in range(0, len(blocks), 100):
            batch = blocks[i:i+100]
            payload["children"] = batch
            
            # Create the page
            response = requests.post(
                f"{self.base_url}/pages",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            page_id = response.json()["id"]
            logger.info(f"Created page with ID: {page_id}")
            
            # Add remaining blocks
            if i + 100 < len(blocks):
                for j in range(i + 100, len(blocks), 100):
                    batch = blocks[j:j+100]
                    response = requests.patch(
                        f"{self.base_url}/blocks/{page_id}/children",
                        headers=self.headers,
                        json={"children": batch}
                    )
                    response.raise_for_status()
                    logger.info(f"Added batch of {len(batch)} blocks to page")
        
        # Return the page ID
        return page_id
    
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
    
    def _get_mime_type(self, file_name: str) -> str:
        """
        Get MIME type based on file name
        
        Args:
            file_name: File name
            
        Returns:
            MIME type string
        """
        extension = file_name.lower().split('.')[-1]
        mime_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        return mime_types.get(extension, 'application/octet-stream')
    
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
        
        try:
            # Check if Storage service is available
            if self.storage_service:
                # Upload image to GCS
                image_url = self.storage_service.upload_image(image_path)
                if image_url:
                    logger.info(f"Image uploaded to GCS: {image_url}")
                    return image_url
                else:
                    logger.warning(f"Failed to upload image to GCS, returning local path as fallback")
                    # 返回本地路徑作為備用選項，這樣至少可以在開發環境中看到圖片
                    return f"file://{image_path}"
            else:
                logger.warning("Storage service is not available, returning local path as fallback")
                # 返回本地路徑作為備用選項
                return f"file://{image_path}"
        
        except Exception as e:
            logger.error(f"Error uploading image to GCS: {str(e)}")
            # 返回本地路徑作為備用選項
            return f"file://{image_path}"

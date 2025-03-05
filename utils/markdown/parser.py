"""
Markdown parser for the class report application.
"""
import re
from typing import List, Dict, Any
from utils.common.logging_utils import get_logger

logger = get_logger(__name__)

class MarkdownParser:
    """
    Parser for Markdown text to Notion format.
    """
    
    def parse_line(self, line: str) -> List[Dict[str, Any]]:
        """
        Parse a single line of markdown and convert to Notion rich text format.
        
        Args:
            line: A line of markdown text
            
        Returns:
            List of rich text objects
        """
        # 使用位置信息來跟踪和排序文本片段
        segments = []
        
        # 處理 Markdown 格式的連結 [text](url)
        for match in re.finditer(r'\[(.*?)\]\((.*?)\)', line):
            text, url = match.groups()
            start, end = match.span()
            segments.append({
                "start": start,
                "end": end,
                "text": text,
                "type": "link",
                "url": url
            })
        
        # 處理粗體和斜體文本 ***text***
        for match in re.finditer(r'\*\*\*(.*?)\*\*\*', line):
            text = match.group(1)
            start, end = match.span()
            segments.append({
                "start": start,
                "end": end,
                "text": text,
                "type": "bold_italic"
            })
        
        # 處理粗體文本 **text**
        for match in re.finditer(r'\*\*(.*?)\*\*', line):
            text = match.group(1)
            start, end = match.span()
            segments.append({
                "start": start,
                "end": end,
                "text": text,
                "type": "bold"
            })
        
        # 處理斜體文本 *text*
        for match in re.finditer(r'(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)', line):
            text = match.group(1)
            start, end = match.span()
            segments.append({
                "start": start,
                "end": end,
                "text": text,
                "type": "italic"
            })
        
        # 處理純 URL
        for match in re.finditer(r'(https?://[^\s]+|www\.[^\s]+)', line):
            url = match.group(1)
            start, end = match.span()
            segments.append({
                "start": start,
                "end": end,
                "text": url,
                "type": "url",
                "url": url if not url.startswith("www.") else "https://" + url
            })
        
        # 按照起始位置排序段落
        segments.sort(key=lambda x: x["start"])
        
        # 檢查重疊並移除重疊的段落
        non_overlapping = []
        for segment in segments:
            # 檢查是否與前一個段落重疊
            if non_overlapping and segment["start"] < non_overlapping[-1]["end"]:
                continue
            non_overlapping.append(segment)
        
        # 填充未標記的文本
        result_segments = []
        last_end = 0
        
        for segment in non_overlapping:
            # 添加段落前的普通文本
            if segment["start"] > last_end:
                result_segments.append({
                    "type": "plain",
                    "text": line[last_end:segment["start"]]
                })
            
            # 添加格式化的段落
            result_segments.append(segment)
            last_end = segment["end"]
        
        # 添加最後的普通文本
        if last_end < len(line):
            result_segments.append({
                "type": "plain",
                "text": line[last_end:]
            })
        
        # 轉換為 Notion 格式
        rich_text = []
        for segment in result_segments:
            if segment["type"] == "plain":
                if segment["text"]:  # 只有在文本非空時添加
                    rich_text.append({
                        "type": "text",
                        "text": {"content": segment["text"]}
                    })
            elif segment["type"] == "bold":
                rich_text.append({
                    "type": "text",
                    "text": {"content": segment["text"]},
                    "annotations": {"bold": True}
                })
            elif segment["type"] == "italic":
                rich_text.append({
                    "type": "text",
                    "text": {"content": segment["text"]},
                    "annotations": {"italic": True}
                })
            elif segment["type"] == "bold_italic":
                rich_text.append({
                    "type": "text",
                    "text": {"content": segment["text"]},
                    "annotations": {"bold": True, "italic": True}
                })
            elif segment["type"] == "link":
                rich_text.append({
                    "type": "text",
                    "text": {
                        "content": segment["text"],
                        "link": {"url": segment["url"]}
                    }
                })
            elif segment["type"] == "url":
                rich_text.append({
                    "type": "text",
                    "text": {
                        "content": segment["text"],
                        "link": {"url": segment["url"]}
                    }
                })
        
        return rich_text
    
    def process_content(self, content: List[str]) -> List[Dict[str, Any]]:
        """
        Process markdown content and convert to Notion blocks.
        
        Args:
            content: List of markdown content lines
            
        Returns:
            List of Notion blocks
        """
        blocks = []
        current_text = ""
        in_quote = False
        in_list = False
        list_items = []
        
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
                            "rich_text": self.parse_line(current_text)
                        }
                    })
                    current_text = ""
                
                # If we were in a list, add the list items now
                if in_list and list_items:
                    for item in list_items:
                        blocks.append({
                            "object": "block",
                            "type": "bulleted_list_item",
                            "bulleted_list_item": {
                                "rich_text": self.parse_line(item)
                            }
                        })
                    list_items = []
                    in_list = False
                
                continue
            
            # Special handling for lines that are just URLs
            # If the line is just a URL, create a bookmark block instead of a paragraph
            url_only_pattern = r'^(https?://[^\s]+)$'
            url_match = re.match(url_only_pattern, line)
            if url_match:
                # Flush any accumulated text
                if current_text:
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": self.parse_line(current_text)
                        }
                    })
                    current_text = ""
                
                # Check if it's a YouTube URL
                youtube_patterns = [
                    r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]+)',
                    r'(?:https?:\/\/)?(?:www\.)?youtu\.be\/([a-zA-Z0-9_-]+)'
                ]
                
                is_youtube = False
                for pattern in youtube_patterns:
                    youtube_match = re.match(pattern, url_match.group(1))
                    if youtube_match:
                        is_youtube = True
                        video_id = youtube_match.group(1)
                        # Add as a video block
                        blocks.append({
                            "object": "block",
                            "type": "video",
                            "video": {
                                "type": "external",
                                "external": {
                                    "url": f"https://www.youtube.com/watch?v={video_id}"
                                }
                            }
                        })
                        break
                
                # If not a YouTube URL, add as a bookmark
                if not is_youtube:
                    blocks.append({
                        "object": "block",
                        "type": "bookmark",
                        "bookmark": {
                            "url": url_match.group(1)
                        }
                    })
                continue
            
            # Process headings with emoji and color
            if line.startswith('# '):
                # Flush any accumulated text
                if current_text:
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": self.parse_line(current_text)
                        }
                    })
                    current_text = ""
                
                # Add heading with emoji based on content
                heading_text = line[2:].strip()
                emoji = "🔔"  # Default emoji
                
                # Choose emoji based on heading content
                if "詩歌" in heading_text or "歌曲" in heading_text or "音樂" in heading_text:
                    emoji = "🎵"
                elif "主題" in heading_text or "主旨" in heading_text:
                    emoji = "👑"
                elif "啟示" in heading_text or "啟發" in heading_text:
                    emoji = "✨"
                elif "活動" in heading_text or "遊戲" in heading_text:
                    emoji = "🎮"
                elif "故事" in heading_text or "聖經" in heading_text:
                    emoji = "📖"
                
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": f"{emoji} {heading_text}"
                                }
                            }
                        ],
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
                            "rich_text": self.parse_line(current_text)
                        }
                    })
                    current_text = ""
                
                # Add subheading
                heading_text = line[3:].strip()
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": self.parse_line(heading_text),
                        "color": "blue_background"
                    }
                })
                continue
            
            # Process numbered lists (e.g., "1. Item")
            numbered_list_match = re.match(r'^\d+\.\s+(.*)', line)
            if numbered_list_match:
                # Flush any accumulated text
                if current_text:
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": self.parse_line(current_text)
                        }
                    })
                    current_text = ""
                
                # Add numbered list item
                list_text = numbered_list_match.group(1)
                blocks.append({
                    "object": "block",
                    "type": "numbered_list_item",
                    "numbered_list_item": {
                        "rich_text": self.parse_line(list_text)
                    }
                })
                continue
            
            # Process list items
            if line.startswith('- ') or line.startswith('* '):
                # Flush any accumulated text
                if current_text:
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": self.parse_line(current_text)
                        }
                    })
                    current_text = ""
                
                # Add to list items
                list_text = line[2:].strip()
                list_items.append(list_text)
                in_list = True
                continue
            
            # Process blockquotes
            elif line.startswith('> '):
                quote_text = line[2:].strip()
                
                # If we're not already in a quote, start a new one
                if not in_quote:
                    # Flush any accumulated text
                    if current_text:
                        blocks.append({
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": self.parse_line(current_text)
                            }
                        })
                        current_text = ""
                    
                    # Start a new quote
                    blocks.append({
                        "object": "block",
                        "type": "quote",
                        "quote": {
                            "rich_text": self.parse_line(quote_text)
                        }
                    })
                    in_quote = True
                else:
                    # Continue the existing quote - add a line break and the new text
                    # First add a line break
                    blocks[-1]["quote"]["rich_text"].append({
                        "type": "text",
                        "text": {"content": "\n"}
                    })
                    # Then add the new text
                    blocks[-1]["quote"]["rich_text"].extend(self.parse_line(quote_text))
                
                continue
            
            # If we reach here, it's a regular paragraph
            if in_quote:
                # End the quote
                in_quote = False
            
            # Process horizontal rule (---)
            if re.match(r'^-{3,}$', line):
                # Flush any accumulated text
                if current_text:
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": self.parse_line(current_text)
                        }
                    })
                    current_text = ""
                
                # Add divider block
                blocks.append({
                    "object": "block",
                    "type": "divider",
                    "divider": {}
                })
                continue
            
            # Accumulate text
            if current_text:
                current_text += " " + line
            else:
                current_text = line
        
        # Add any remaining text
        if current_text:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": self.parse_line(current_text)
                }
            })
        
        # Add any remaining list items
        if in_list and list_items:
            for item in list_items:
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": self.parse_line(item)
                    }
                })
        
        return blocks 
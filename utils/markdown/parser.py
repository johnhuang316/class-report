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
        
        # 處理 Markdown 格式的連結 [text](url) - 改進連結檢測
        for match in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', line):
            text, url = match.groups()
            start, end = match.span()
            segments.append({
                "start": start,
                "end": end,
                "text": text,
                "type": "link",
                "url": url
            })
        
        # 處理粗體和斜體文本 ***text*** - 改進巢狀格式處理
        for match in re.finditer(r'\*\*\*((?:[^*]|\*(?!\*\*))*)\*\*\*', line):
            text = match.group(1)
            start, end = match.span()
            segments.append({
                "start": start,
                "end": end,
                "text": text,
                "type": "bold_italic"
            })
        
        # 處理粗體文本 **text** - 改進巢狀格式處理
        for match in re.finditer(r'\*\*((?:[^*]|\*(?!\*))*)\*\*', line):
            text = match.group(1)
            start, end = match.span()
            # 確保這不是 ***text*** 的一部分
            is_part_of_bold_italic = False
            for segment in segments:
                if segment["type"] == "bold_italic" and start >= segment["start"] and end <= segment["end"]:
                    is_part_of_bold_italic = True
                    break
            
            if not is_part_of_bold_italic:
                segments.append({
                    "start": start,
                    "end": end,
                    "text": text,
                    "type": "bold"
                })
        
        # 處理斜體文本 *text* - 改進巢狀格式處理
        for match in re.finditer(r'(?<!\*)\*((?:[^*]|\*(?!\*))*)\*(?!\*)', line):
            text = match.group(1)
            start, end = match.span()
            segments.append({
                "start": start,
                "end": end,
                "text": text,
                "type": "italic"
            })
        
        # 處理純 URL - 改進 URL 檢測
        url_pattern = r'((?:https?://[^\s<>"]+)|(?:www\.[^\s<>"]+))'
        for match in re.finditer(url_pattern, line):
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
        
        # 改進重疊檢測邏輯
        non_overlapping = []
        for segment in segments:
            # 檢查是否與前一個段落重疊
            if non_overlapping:
                prev = non_overlapping[-1]
                # 如果當前段落與前一個段落重疊，選擇較長的那個
                if segment["start"] < prev["end"]:
                    if (segment["end"] - segment["start"]) > (prev["end"] - prev["start"]):
                        non_overlapping[-1] = segment
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
        in_code_block = False
        code_block_content = []
        code_language = ""
        
        def process_blockquote_list_item(rich_text_list, list_text):
            """Helper function to process list items within blockquotes"""
            # Check for bold text pattern in list items
            bold_pattern = re.match(r'^\*\*(.*?)\*\*:?(.*)', list_text)
            if bold_pattern:
                bold_text = bold_pattern.group(1)
                remaining_text = bold_pattern.group(2).strip()
                
                # Add a line break and the list item with bullet
                rich_text_list.append({
                    "type": "text",
                    "text": {"content": "\n• "}
                })
                
                # Add the bold part
                rich_text_list.append({
                    "type": "text",
                    "text": {"content": bold_text},
                    "annotations": {"bold": True}
                })
                
                # Add colon if present
                if ":" in list_text and remaining_text:
                    rich_text_list.append({
                        "type": "text",
                        "text": {"content": ": "}
                    })
                
                # Add the remaining text
                if remaining_text:
                    rich_text_list.extend(self.parse_line(remaining_text))
            else:
                # Regular list item
                # Add a line break and the list item with bullet
                rich_text_list.append({
                    "type": "text",
                    "text": {"content": "\n• "}
                })
                rich_text_list.extend(self.parse_line(list_text))
        
        i = 0
        while i < len(content):
            line = content[i].rstrip()
            
            # Handle code blocks
            if line.startswith("```"):
                # Start or end of code block
                if not in_code_block:
                    # Starting a new code block
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
                    
                    in_code_block = True
                    code_block_content = []
                    # Check if language is specified
                    if len(line) > 3:
                        code_language = line[3:].strip().lower()  # 改進：統一轉換為小寫
                        # 改進：標準化程式語言名稱
                        language_mapping = {
                            'js': 'javascript',
                            'py': 'python',
                            'rb': 'ruby',
                            'ts': 'typescript',
                            'cs': 'csharp',
                            'html': 'html',
                            'css': 'css',
                            'sh': 'shell',
                            'bash': 'shell',
                            'json': 'json',
                            'md': 'markdown'
                        }
                        code_language = language_mapping.get(code_language, code_language)
                    else:
                        code_language = ""
                else:
                    # Ending a code block
                    code_text = "\n".join(code_block_content)
                    blocks.append({
                        "object": "block",
                        "type": "code",
                        "code": {
                            "rich_text": [{
                                "type": "text",
                                "text": {"content": code_text}
                            }],
                            "language": code_language if code_language else "plain_text"
                        }
                    })
                    in_code_block = False
                    code_block_content = []
                    code_language = ""
                i += 1
                continue
            
            # If we're in a code block, add the line to the code content
            if in_code_block:
                code_block_content.append(line)
                i += 1
                continue
            
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
                
                i += 1
                continue
            
            # 改進的 YouTube 連結檢測
            youtube_patterns = [
                r'^\s*\[(.*?)\]\((https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]+)(?:[^\)]*?))\)\s*$',
                r'^\s*https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]+)(?:[^\s]*?)\s*$'
            ]
            
            is_youtube = False
            for pattern in youtube_patterns:
                youtube_match = re.match(pattern, line)
                if youtube_match:
                    is_youtube = True
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
                    
                    # Extract video ID and create URL
                    if len(youtube_match.groups()) > 2:  # Markdown format
                        video_url = youtube_match.group(2)
                    else:  # Direct URL format
                        video_id = youtube_match.group(1)
                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                    
                    # Add as a video block
                    blocks.append({
                        "object": "block",
                        "type": "video",
                        "video": {
                            "type": "external",
                            "external": {
                                "url": video_url
                            }
                        }
                    })
                    break
            
            if is_youtube:
                i += 1
                continue
            
            # 改進的 URL 檢測
            url_pattern = r'^((?:https?://[^\s<>"]+)|(?:www\.[^\s<>"]+))$'
            url_match = re.match(url_pattern, line)
            if url_match and not is_youtube:
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
                
                url = url_match.group(1)
                if url.startswith("www."):
                    url = "https://" + url
                
                blocks.append({
                    "object": "block",
                    "type": "bookmark",
                    "bookmark": {
                        "url": url
                    }
                })
                i += 1
                continue
            
            # 改進的標題檢測和表情符號選擇
            heading_match = re.match(r'^(#{1,6})(?:\s+|\s*(?=[^\s#]))(.*?)(?:\s+#*)?$', line)
            if heading_match:
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
                
                heading_level = len(heading_match.group(1))
                heading_text = heading_match.group(2).strip()
                
                # 改進的表情符號選擇邏輯
                emoji_mapping = {
                    r'(?:詩歌|歌曲|音樂|讚美|敬拜)': "🎵",
                    r'(?:主題|主旨|重點|核心|目標)': "👑",
                    r'(?:啟示|啟發|亮光|領受|感動)': "✨",
                    r'(?:活動|遊戲|互動|分組|團康)': "🎮",
                    r'(?:故事|聖經|經文|信息|見證)': "📖",
                    r'(?:禱告|祈禱|代禱|守望)': "🙏",
                    r'(?:分享|交流|討論|回應)': "💝",
                    r'(?:問題|思考|反思|探討)': "💭",
                    r'(?:總結|結論|回顧|整理)': "📝",
                    r'(?:時間|日期|行程|安排)': "⏰",
                    r'(?:地點|場地|位置)': "📍",
                    r'(?:人員|同工|服事|配搭)': "👥"
                }
                
                emoji = "🔔"  # 預設表情符號
                for pattern, e in emoji_mapping.items():
                    if re.search(pattern, heading_text, re.IGNORECASE):
                        emoji = e
                        break
                
                # 根據層級決定標題類型
                if heading_level == 1:
                    heading_type = "heading_2"  # h1 映射到 Notion 的 heading_2
                elif heading_level == 2:
                    heading_type = "heading_3"  # h2 映射到 Notion 的 heading_3
                else:
                    heading_type = "heading_3"  # h3+ 預設為 heading_3
                
                blocks.append({
                    "object": "block",
                    "type": heading_type,
                    heading_type: {
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
                i += 1
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
                i += 1
                continue
            
            # Process numbered lists (e.g., "1. Item")
            numbered_list_match = re.match(r'^(\s*)(\d+)\.[\s]+(.*)', line)
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
                
                # Get indentation level and list text
                indent = len(numbered_list_match.group(1))
                number = numbered_list_match.group(2)
                list_text = numbered_list_match.group(3)
                
                # Add numbered list item
                blocks.append({
                    "object": "block",
                    "type": "numbered_list_item",
                    "numbered_list_item": {
                        "rich_text": self.parse_line(list_text)
                    }
                })
                
                # Check for indented text following the numbered list item
                j = i + 1
                indented_content = []
                
                while j < len(content) and content[j].strip():
                    next_line = content[j].rstrip()
                    
                    # Check if it's an indented line (starts with spaces)
                    indented_match = re.match(r'^(\s+)(.+)', next_line)
                    if indented_match and not next_line.lstrip().startswith(('- ', '* ', '• ', '1. ', '2. ', '3. ')):
                        next_indent = len(indented_match.group(1))
                        if next_indent > indent:
                            # This is indented text belonging to the list item
                            indented_text = indented_match.group(2)
                            indented_content.append(indented_text)
                            j += 1
                        else:
                            break
                    else:
                        break
                
                # If we found indented content, add it to the list item
                if indented_content:
                    # Add the indented content as a paragraph block inside the list item
                    if "children" not in blocks[-1]["numbered_list_item"]:
                        blocks[-1]["numbered_list_item"]["children"] = []
                    
                    blocks[-1]["numbered_list_item"]["children"].append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": self.parse_line(" ".join(indented_content))
                        }
                    })
                    
                    i = j
                else:
                    i += 1
                
                continue
            
            # Process list items (including indented ones)
            list_item_match = re.match(r'^(\s*)[•\-\*]\s+(.*)', line)
            if list_item_match:
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
                
                # Get indentation level and list text
                indent = len(list_item_match.group(1))
                list_text = list_item_match.group(2)
                
                # Add as bulleted list item
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": self.parse_line(list_text)
                    }
                })
                
                # Check for sub-items (indented list items)
                j = i + 1
                while j < len(content) and content[j].strip():
                    sub_item_match = re.match(r'^(\s+)[\-\*]\s+(.*)', content[j])
                    if sub_item_match and len(sub_item_match.group(1)) > indent:
                        # This is a sub-item
                        sub_text = sub_item_match.group(2)
                        
                        # Add as a child of the current list item
                        if "children" not in blocks[-1]["bulleted_list_item"]:
                            blocks[-1]["bulleted_list_item"]["children"] = []
                        
                        blocks[-1]["bulleted_list_item"]["children"].append({
                            "object": "block",
                            "type": "bulleted_list_item",
                            "bulleted_list_item": {
                                "rich_text": self.parse_line(sub_text)
                            }
                        })
                        j += 1
                    else:
                        break
                
                i = j
                continue
            
            # Process blockquotes
            elif line.startswith('> ') or re.match(r'^>\d+\.', line) or re.match(r'^>-', line) or line.startswith('>'):
                # Handle blockquotes that start with ">N." (without space after ">")
                if re.match(r'^>(\d+)\.', line):
                    match = re.match(r'^>(\d+)\.(.*)', line)
                    quote_text = match.group(1) + "." + match.group(2).strip()
                # Handle blockquotes that start with ">-" (without space after ">")
                elif re.match(r'^>-', line):
                    match = re.match(r'^>-(.*)', line)
                    quote_text = "- " + match.group(1).strip()
                # Handle any blockquote that just starts with ">" (without any space)
                elif line.startswith('>') and not line.startswith('> '):
                    quote_text = line[1:].strip()
                else:
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
                
                # Check if the next line is also a quote or a list item within a quote
                j = i + 1
                while j < len(content):
                    next_line = content[j].rstrip()
                    if next_line.startswith('> '):
                        # It's a continuation of the quote
                        next_quote_text = next_line[2:].strip()
                        
                        # Add a line break and the new text
                        blocks[-1]["quote"]["rich_text"].append({
                            "type": "text",
                            "text": {"content": "\n"}
                        })
                        
                        # Check for special formatting in the quote text
                        if next_quote_text.startswith('**') and next_quote_text.endswith('**'):
                            # Bold text in quote
                            bold_text = next_quote_text[2:-2]
                            blocks[-1]["quote"]["rich_text"].append({
                                "type": "text",
                                "text": {"content": bold_text},
                                "annotations": {"bold": True}
                            })
                        else:
                            # Regular text
                            blocks[-1]["quote"]["rich_text"].extend(self.parse_line(next_quote_text))
                        
                        j += 1
                    elif next_line.startswith('> - ') or next_line.startswith('> * ') or next_line.startswith('> • '):
                        # It's a list item within a quote
                        list_text = next_line[4:].strip()
                        process_blockquote_list_item(blocks[-1]["quote"]["rich_text"], list_text)
                        j += 1
                    elif re.match(r'^>[*\-•]', next_line):
                        # It's a list item within a quote without space after >
                        list_text = next_line[2:].strip()
                        process_blockquote_list_item(blocks[-1]["quote"]["rich_text"], list_text)
                        j += 1
                    elif next_line.startswith('>'):
                        # It's an empty line in the quote (just '>') or a line without space after >
                        if len(next_line) > 1:
                            # Line without space after >
                            next_quote_text = next_line[1:].strip()
                            blocks[-1]["quote"]["rich_text"].append({
                                "type": "text",
                                "text": {"content": "\n"}
                            })
                            blocks[-1]["quote"]["rich_text"].extend(self.parse_line(next_quote_text))
                        else:
                            # Empty line in quote
                            blocks[-1]["quote"]["rich_text"].append({
                                "type": "text",
                                "text": {"content": "\n"}
                            })
                        j += 1
                    else:
                        break
                
                i = j
                continue
            
            # If we reach here, it's a regular paragraph
            if in_quote:
                # End the quote
                in_quote = False
            
            # Process horizontal rule (---)
            if re.match(r'^-{3,}$', line) or line == '---':
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
                i += 1
                continue
            
            # Process nested blockquotes (e.g., "> > text")
            nested_quote_match = re.match(r'^>\s+>\s+(.*)', line)
            if nested_quote_match:
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
                
                # Add nested quote with indentation
                nested_text = nested_quote_match.group(1)
                blocks.append({
                    "object": "block",
                    "type": "quote",
                    "quote": {
                        "rich_text": self.parse_line("    " + nested_text)
                    }
                })
                i += 1
                continue
            
            # Accumulate text
            if current_text:
                current_text += " " + line
            else:
                current_text = line
            
            i += 1
        
        # Handle any unclosed code block at the end
        if in_code_block and code_block_content:
            code_text = "\n".join(code_block_content)
            blocks.append({
                "object": "block",
                "type": "code",
                "code": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": code_text}
                    }],
                    "language": code_language if code_language else "plain_text"
                }
            })
        
        # Add any remaining text
        if current_text:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": self.parse_line(current_text)
                }
            })
        
        return blocks

"""
Markdown parser for the class report application.
"""
from dataclasses import dataclass
from enum import Enum
import re
from typing import List, Dict, Any, Optional, Tuple

from utils.common.logging_utils import get_logger

logger = get_logger(__name__)

class BlockType(Enum):
    """Block types supported by the parser."""
    PARAGRAPH = "paragraph"
    HEADING_2 = "heading_2"
    HEADING_3 = "heading_3"
    BULLETED_LIST_ITEM = "bulleted_list_item"
    NUMBERED_LIST_ITEM = "numbered_list_item"
    QUOTE = "quote"
    CODE = "code"
    DIVIDER = "divider"
    VIDEO = "video"
    BOOKMARK = "bookmark"

class TextType(Enum):
    """Text types supported by the parser."""
    PLAIN = "plain"
    BOLD = "bold"
    ITALIC = "italic"
    BOLD_ITALIC = "bold_italic"
    LINK = "link"
    URL = "url"

@dataclass
class TextSegment:
    """Represents a segment of text with formatting."""
    start: int
    end: int
    text: str
    type: TextType
    url: Optional[str] = None

@dataclass
class Block:
    """Represents a Notion block."""
    type: BlockType
    content: Dict[str, Any]

class MarkdownParser:
    """Parser for Markdown text to Notion format."""
    
    # Regex patterns
    PATTERNS = {
        'link': r'\[([^\]]+)\]\(([^)]+)\)',
        'bold_italic': r'\*\*\*((?:[^*]|\*(?!\*\*))*)\*\*\*',
        'bold': r'\*\*((?:[^*]|\*(?!\*))*)\*\*',
        'italic': r'(?<!\*)\*((?:[^*]|\*(?!\*))*)\*(?!\*)',
        'url': r'((?:https?://[^\s<>"]+)|(?:www\.[^\s<>"]+))',
        'youtube': [
            r'^\s*\[(.*?)\]\((https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/))([a-zA-Z0-9_-]+)(?:[^\)]*?))\)\s*$',
            r'^\s*https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)([a-zA-Z0-9_-]+)(?:[^\s]*?)\s*$'
        ],
        'heading': r'^(#{1,6})(?:\s+|\s*(?=[^\s#]))(.*?)(?:\s+#*)?$',
        'numbered_list': r'^(\s*)(\d+)\.[\s]+(.*)',
        'list_item': r'^(\s*)[•\-\*]\s+(.*)',
        'blockquote': r'^>\s*(.*)',
        'nested_blockquote': r'^>\s+>\s+(.*)',
        'horizontal_rule': r'^-{3,}$'
    }

    # Emoji mapping for headings
    EMOJI_MAPPING = {
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

    def __init__(self):
        """Initialize the parser."""
        self.blocks: List[Block] = []
        self.current_text = ""
        self.in_quote = False
        self.in_code_block = False
        self.code_block_content: List[str] = []
        self.code_language = ""

    def _find_text_segments(self, line: str) -> List[TextSegment]:
        """Find all text segments in a line with their formatting."""
        segments = []
        
        # Find links
        for match in re.finditer(self.PATTERNS['link'], line):
            text, url = match.groups()
            start, end = match.span()
            segments.append(TextSegment(start, end, text, TextType.LINK, url))
        
        # Find bold_italic text
        for match in re.finditer(self.PATTERNS['bold_italic'], line):
            text = match.group(1)
            start, end = match.span()
            segments.append(TextSegment(start, end, text, TextType.BOLD_ITALIC))
        
        # Find bold text
        for match in re.finditer(self.PATTERNS['bold'], line):
            text = match.group(1)
            start, end = match.span()
            if not any(s.type == TextType.BOLD_ITALIC and start >= s.start and end <= s.end for s in segments):
                segments.append(TextSegment(start, end, text, TextType.BOLD))
        
        # Find italic text
        for match in re.finditer(self.PATTERNS['italic'], line):
            text = match.group(1)
            start, end = match.span()
            segments.append(TextSegment(start, end, text, TextType.ITALIC))
        
        # Find URLs
        for match in re.finditer(self.PATTERNS['url'], line):
            url = match.group(1)
            start, end = match.span()
            segments.append(TextSegment(
                start, end, url, TextType.URL,
                url if not url.startswith("www.") else f"https://{url}"
            ))
        
        return sorted(segments, key=lambda x: x.start)

    def _create_rich_text(self, segment: TextSegment) -> Dict[str, Any]:
        """Create a rich text object from a text segment."""
        rich_text = {
            "type": "text",
            "text": {"content": segment.text}
        }
        
        if segment.type == TextType.BOLD:
            rich_text["annotations"] = {"bold": True}
        elif segment.type == TextType.ITALIC:
            rich_text["annotations"] = {"italic": True}
        elif segment.type == TextType.BOLD_ITALIC:
            rich_text["annotations"] = {"bold": True, "italic": True}
        elif segment.type in (TextType.LINK, TextType.URL):
            rich_text["text"]["link"] = {"url": segment.url}
        
        return rich_text

    def _parse_line_to_rich_text(self, line: str) -> List[Dict[str, Any]]:
        """Parse a line to Notion rich text format."""
        segments = self._find_text_segments(line)
        rich_text = []
        last_end = 0
        
        for segment in segments:
            # Add plain text before the segment
            if segment.start > last_end:
                rich_text.append({
                    "type": "text",
                    "text": {"content": line[last_end:segment.start]}
                })
            
            # Add the formatted segment
            rich_text.append(self._create_rich_text(segment))
            last_end = segment.end
        
        # Add remaining plain text
        if last_end < len(line):
            rich_text.append({
                "type": "text",
                "text": {"content": line[last_end:]}
            })
        
        return rich_text

    def _get_heading_emoji(self, text: str) -> str:
        """Get appropriate emoji for heading text."""
        for pattern, emoji in self.EMOJI_MAPPING.items():
            if re.search(pattern, text, re.IGNORECASE):
                return emoji
        return "🔔"

    def _create_heading_block(self, level: int, text: str) -> Block:
        """Create a heading block."""
        heading_type = BlockType.HEADING_2 if level == 1 else BlockType.HEADING_3
        emoji = self._get_heading_emoji(text)
        
        return Block(
            type=heading_type,
            content={
                "rich_text": [{
                    "type": "text",
                    "text": {"content": f"{emoji} {text}"}
                }],
                "color": "blue_background"
            }
        )

    def _create_list_item_block(self, text: str, is_numbered: bool = False) -> Block:
        """Create a list item block."""
        block_type = BlockType.NUMBERED_LIST_ITEM if is_numbered else BlockType.BULLETED_LIST_ITEM
        return Block(
            type=block_type,
            content={"rich_text": self._parse_line_to_rich_text(text)}
        )

    def _create_quote_block(self, text: str) -> Block:
        """Create a quote block."""
        return Block(
            type=BlockType.QUOTE,
            content={"rich_text": self._parse_line_to_rich_text(text)}
        )

    def _create_code_block(self, code: str, language: str = "") -> Block:
        """Create a code block."""
        return Block(
            type=BlockType.CODE,
            content={
                "rich_text": [{"type": "text", "text": {"content": code}}],
                "language": language if language else "plain_text"
            }
        )

    def _flush_current_text(self) -> None:
        """Flush accumulated text as a paragraph block."""
        if self.current_text:
            self.blocks.append(Block(
                type=BlockType.PARAGRAPH,
                content={"rich_text": self._parse_line_to_rich_text(self.current_text)}
            ))
            self.current_text = ""

    def process_content(self, content: List[str]) -> List[Dict[str, Any]]:
        """
        Process markdown content and convert to Notion blocks.
        
        Args:
            content: List of markdown content lines
            
        Returns:
            List of Notion blocks
        """
        self.blocks = []
        self.current_text = ""
        self.in_quote = False
        self.in_code_block = False
        self.code_block_content = []
        self.code_language = ""
        
        # 預處理：檢查並提取所有獨立行的 YouTube 連結
        youtube_lines = []
        processed_content = []
        
        for line in content:
            line = line.rstrip()
            youtube_match1 = re.match(self.PATTERNS['youtube'][0], line)
            youtube_match2 = re.match(self.PATTERNS['youtube'][1], line)
            
            if youtube_match1 or youtube_match2:
                youtube_lines.append(line)
                # 添加一個空行作為佔位符，以保持行號一致
                processed_content.append("")
            else:
                processed_content.append(line)
        
        i = 0
        while i < len(processed_content):
            line = processed_content[i].rstrip()
            
            # Skip empty lines
            if not line:
                self._flush_current_text()
                
                # 檢查這是否是 YouTube 連結的佔位符
                if i < len(content) and (
                    re.match(self.PATTERNS['youtube'][0], content[i].rstrip()) or 
                    re.match(self.PATTERNS['youtube'][1], content[i].rstrip())
                ):
                    original_line = content[i].rstrip()
                    youtube_match1 = re.match(self.PATTERNS['youtube'][0], original_line)
                    youtube_match2 = re.match(self.PATTERNS['youtube'][1], original_line)
                    
                    if youtube_match1:
                        text, url, video_id = youtube_match1.groups()
                        self.blocks.append(Block(
                            type=BlockType.VIDEO,
                            content={
                                "type": "external",
                                "external": {
                                    "url": f"https://www.youtube.com/watch?v={video_id}"
                                }
                            }
                        ))
                    elif youtube_match2:
                        video_id = youtube_match2.group(1)
                        self.blocks.append(Block(
                            type=BlockType.VIDEO,
                            content={
                                "type": "external",
                                "external": {
                                    "url": f"https://www.youtube.com/watch?v={video_id}"
                                }
                            }
                        ))
                
                i += 1
                continue
            
            # Handle code blocks
            if line.startswith("```"):
                if not self.in_code_block:
                    self._flush_current_text()
                    self.in_code_block = True
                    if len(line) > 3:
                        self.code_language = line[3:].strip().lower()
                else:
                    code_text = "\n".join(self.code_block_content)
                    self.blocks.append(self._create_code_block(code_text, self.code_language))
                    self.in_code_block = False
                    self.code_block_content = []
                    self.code_language = ""
                i += 1
                continue
            
            if self.in_code_block:
                self.code_block_content.append(line)
                i += 1
                continue
            
            # Handle headings
            heading_match = re.match(self.PATTERNS['heading'], line)
            if heading_match:
                self._flush_current_text()
                level = len(heading_match.group(1))
                text = heading_match.group(2).strip()
                self.blocks.append(self._create_heading_block(level, text))
                i += 1
                continue
            
            # Handle lists
            list_match = re.match(self.PATTERNS['list_item'], line)
            if list_match:
                self._flush_current_text()
                text = list_match.group(2)
                self.blocks.append(self._create_list_item_block(text))
                i += 1
                continue
            
            # Handle numbered lists
            numbered_match = re.match(self.PATTERNS['numbered_list'], line)
            if numbered_match:
                self._flush_current_text()
                text = numbered_match.group(3)
                self.blocks.append(self._create_list_item_block(text, is_numbered=True))
                i += 1
                continue
            
            # Handle blockquotes
            quote_match = re.match(self.PATTERNS['blockquote'], line)
            if quote_match:
                self._flush_current_text()
                text = quote_match.group(1)
                if not self.in_quote:
                    self.blocks.append(self._create_quote_block(text))
                    self.in_quote = True
                else:
                    self.blocks[-1].content["rich_text"].append({
                        "type": "text",
                        "text": {"content": "\n"}
                    })
                    self.blocks[-1].content["rich_text"].extend(self._parse_line_to_rich_text(text))
                i += 1
                continue
            
            # Handle horizontal rules
            if re.match(self.PATTERNS['horizontal_rule'], line) or line == '---':
                self._flush_current_text()
                self.blocks.append(Block(type=BlockType.DIVIDER, content={}))
                i += 1
                continue
            
            # Accumulate regular text
            if self.current_text:
                self.current_text += " " + line
            else:
                self.current_text = line
            
            i += 1
        
        # Handle any remaining text or code block
        if self.in_code_block and self.code_block_content:
            code_text = "\n".join(self.code_block_content)
            self.blocks.append(self._create_code_block(code_text, self.code_language))
        
        self._flush_current_text()
        
        return [block.content | {"object": "block", "type": block.type.value} for block in self.blocks]

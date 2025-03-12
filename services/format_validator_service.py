import os
import re
import logging
from typing import List, Dict, Any, Tuple
import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FormatValidatorService:
    def __init__(self, api_key: str):
        """
        Initialize the Format Validator service with Gemini API key.
        
        Args:
            api_key: Gemini API key
        """
        logger.info("Initializing FormatValidatorService")
        if not api_key:
            logger.error("API key is empty or None")
            raise ValueError("Gemini API key is required")
        
        # Configure the Gemini API
        genai.configure(api_key=api_key)
        
        # Get the Gemini model
        self.model = genai.GenerativeModel('gemini-2.0-flash-lite')
        logger.info("FormatValidatorService initialized successfully")
    
    def validate_markdown_format(self, content: str) -> Tuple[bool, str]:
        """
        Validate if the markdown content is compatible with Notion and fix any issues.
        
        Args:
            content: Markdown content to validate
            
        Returns:
            Tuple of (is_valid, fixed_content)
        """
        logger.info("Validating Notion format compatibility")
        logger.info(f"Input content length: {len(content)} characters")
        
        # 檢查並修復整個內容被代碼塊包圍的問題
        if content.startswith('```') and content.endswith('```'):
            logger.info("Content is wrapped in code block, removing code block markers")
            content = content[3:-3].strip()
        
        # 檢查是否有多餘的代碼塊標記
        lines = content.split('\n')
        code_block_starts = [i for i, line in enumerate(lines) if line.strip() == '```']
        if len(code_block_starts) % 2 != 0:
            logger.info("Unbalanced code block markers found, fixing...")
            # 如果有奇數個代碼塊標記，移除最後一個
            if code_block_starts:
                lines.pop(code_block_starts[-1])
                content = '\n'.join(lines)
        
        # 檢查並修復 Markdown 圖片語法
        img_pattern = r'!\[(.*?)\]\((.*?)\)'
        if re.search(img_pattern, content):
            logger.info("Found Markdown image syntax, ensuring proper formatting")
            # 確保圖片鏈接有正確的格式
            content = re.sub(img_pattern, r'![\1](\2)', content)
        
        # Create prompt for Gemini
        prompt = f"""
        You are a Markdown format expert. Your task is to check if the following Markdown content is compatible with Notion and fix any compatibility issues.
        
        Here are the Markdown formats supported by Notion:
        1. Headings: # Level 1 Heading, ## Level 2 Heading
        2. Text formatting: **bold**, *italic*, ***bold and italic***
        3. Quotes: > quoted text
        4. Bullet lists: - item or • item
        5. Dividers: ---
        6. Images: ![alt text](image_url) - ensure images have proper syntax
        
        Here are formats NOT supported or with limited support in Notion:
        1. Tables are not supported
        2. Complex nested lists are not supported
        3. HTML tags are not supported
        4. Code blocks with triple backticks (```) are not supported well
        
        IMPORTANT: DO NOT modify or remove any emojis in the content. All emojis should be preserved exactly as they appear in the original text.
        
        IMPORTANT: DO NOT wrap the entire content in code blocks (```). If you see the entire content wrapped in code blocks, remove the code block markers.
        
        IMPORTANT: For images, ensure they have proper Markdown syntax and are on their own line for better rendering.
        
        Please check the following content and fix any compatibility issues. Maintain the original meaning and structure, only modify formatting issues:
        
        ```
        {content}
        ```
        
        Return the fixed content directly without any explanations or comments. If the content is already compatible with Notion, return the original content.
        """
        
        logger.info("Sending validation prompt to Gemini API")
        
        try:
            # Generate content using Gemini
            response = self.model.generate_content([{"text": prompt}])
            logger.info("Received response from Gemini API")
            
            # Process response
            fixed_content = response.text.strip()
            logger.info(f"Response text length: {len(fixed_content)} characters")
            
            if not fixed_content:
                logger.error("Validation result is empty")
                return False, content
            
            # 再次檢查並修復整個內容被代碼塊包圍的問題
            if fixed_content.startswith('```') and fixed_content.endswith('```'):
                logger.info("Fixed content is still wrapped in code block, removing code block markers")
                fixed_content = fixed_content[3:-3].strip()
            
            # Check if content was modified
            is_modified = fixed_content != content
            if is_modified:
                logger.info("Content was modified to fix Notion compatibility issues")
            else:
                logger.info("Content is already compatible with Notion")
            
            return True, fixed_content
            
        except Exception as e:
            logger.error(f"Error validating content with Gemini API: {str(e)}")
            return False, content

    def validate_format(self, content: str) -> Tuple[bool, str]:
        """
        驗證並修復 Markdown 格式
        
        Args:
            content: 要驗證的內容
            
        Returns:
            Tuple[bool, str]: (是否有效, 修復後的內容)
        """
        return self.validate_markdown_format(content)

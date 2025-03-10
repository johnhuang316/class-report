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
        
        # Create prompt for Gemini
        prompt = f"""
        You are a Markdown format expert. Your task is to check if the following Markdown content is compatible with Notion and fix any compatibility issues.
        
        Here are the Markdown formats supported by Notion:
        1. Headings: # Level 1 Heading, ## Level 2 Heading
        2. Text formatting: **bold**, *italic*, ***bold and italic***
        3. Quotes: > quoted text
        4. Bullet lists: - item or • item
        5. Dividers: ---
        
        Here are formats NOT supported or with limited support in Notion:
        1. Tables are not supported
        2. Complex nested lists are not supported
        3. HTML tags are not supported
        
        IMPORTANT: DO NOT modify or remove any emojis in the content. All emojis should be preserved exactly as they appear in the original text.
        
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

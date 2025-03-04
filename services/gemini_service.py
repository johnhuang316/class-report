import google.generativeai as genai
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self, api_key: str):
        """Initialize the Gemini client with the API key."""
        logger.info("Initializing GeminiService")
        if not api_key:
            logger.error("Gemini API key is empty or None")
            raise ValueError("Gemini API key is required")
            
        # Log a masked version of the API key for debugging
        masked_key = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "***"
        logger.info(f"Using Gemini API key: {masked_key}")
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-pro-exp-02-05')
            logger.info("Gemini model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {str(e)}")
            raise
    
    def generate_report(self, content: str) -> str:
        """
        Generate a Sunday School weekly report using the Gemini API based on provided content.
        
        Args:
            content: User input about class activities
            
        Returns:
            Generated report text with paragraphs separated by double newlines
        """
        logger.info("Generating report from content")
        logger.info(f"Input content length: {len(content)} characters")
        
        # Create prompt for Gemini
        prompt = f"""
        你是一位主日學老師助理。你的任務是根據以下來自主日學課堂的筆記，為家長和教會生成一份美觀、溫馨且具有精美版面設計的週報。

        來自課堂筆記的內容：
        {content}

        請基於這些信息生成一份結構化的週報，遵循以下要求：
        1. **最重要：你可以用不同的方式表達原始筆記中的內容，但絕對不能添加任何原始筆記中沒有的信息或細節**
        2. **最重要：報告的結構和內容應完全基於原始筆記中提供的信息，不要強制使用預定義的章節**
        3. **最重要：根據原始筆記的實際內容來組織報告，使用適合的標題和分類，如果用了更適合的標題和分類，就不用按照原文寫**
        4. **重要：必須使用繁體中文**
        5. **重要：內容應該是連貫的文章格式，而不是分散的點**
        6. **重要：每個段落應該有至少3-5句話，形成完整的敘述**
        7. **重要：使用溫馨可愛的語言，適合描述主日學活動**
        8. **重要：注重版面設計和視覺結構，使用表情符號、分隔線和適當的空白來創造美觀的排版**
        9. **重要：要判斷原文當中的一些符號是不是在 notion 能用，不能的話要推論它的意思並用別的符號或文字取代**
        10.**重要：這是課後紀錄，如果來源有課前的預告提醒，要修改表達方式**
        11.**重要：如果紀錄裡有老師的名字，就盡量不要忽略**

        版面設計指南：
        1. 使用 # 和 ## 等標記創建層次分明的標題。
        2. 每個部分標題都應包含表情符號，使內容更加生動活潑
        3. 使用 > 引用格式突出重要信息
        4. 使用 • 或 - 創建項目符號列表
        5. 適當使用 **粗體** 和 *斜體* 強調重要內容
        6. 在各部分之間使用 --- 分隔線創造清晰的視覺分隔
        7. 在報告開頭添加一個溫馨可愛的總體介紹
        8. 要提的神的部分都用"神"這個字，不用要"上帝"
        9. 段落下一行是標題的話，要多加一行換行

        請直接返回完整的週報內容，不要添加任何額外的格式說明或標記。確保最終輸出是一個美觀、結構清晰且充滿愛的主日學週報。
        
        再次強調：你可以改變表達方式和組織結構，但不能添加原始筆記中沒有的信息。所有內容必須來自原始筆記。
        """
        
        logger.info("Sending prompt to Gemini API")
        
        try:
            # Generate content using Gemini
            response = self.model.generate_content([{"text": prompt}])
            logger.info("Received response from Gemini API")
            
            # Process response
            report_text = response.text.strip()
            logger.info(f"Response text length: {len(report_text)} characters")
            
            if not report_text:
                logger.error("Generated report is empty")
                raise ValueError("Gemini API returned empty response")
            
            return report_text
            
        except Exception as e:
            logger.error(f"Error generating content with Gemini API: {str(e)}")
            raise

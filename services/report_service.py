"""
報告生成服務 - 處理報告生成的核心業務邏輯
"""
import logging
from typing import List, Tuple, Dict, Any, Optional

from utils.common.logging_utils import get_logger

logger = get_logger("report_service")

class ReportService:
    """處理報告生成的核心業務邏輯"""
    
    def __init__(self, gemini_service, notion_service, format_validator_service):
        """
        初始化報告服務
        
        Args:
            gemini_service: Gemini AI 服務實例
            notion_service: Notion API 服務實例
            format_validator_service: 格式驗證服務實例
        """
        self.gemini_service = gemini_service
        self.notion_service = notion_service
        self.format_validator_service = format_validator_service
    
    def format_date_for_display(self, date_str: str) -> str:
        """
        將 ISO 格式日期 (YYYY-MM-DD) 轉換為顯示格式 (YYYY年MM月DD日)
        
        Args:
            date_str: ISO 格式的日期字符串
            
        Returns:
            格式化後的日期字符串
        """
        try:
            year = date_str[:4]
            month = date_str[5:7]
            day = date_str[8:10]
            return f"{year}年{month}月{day}日"
        except (IndexError, TypeError):
            # 處理無效日期
            return "未知日期"
    
    def generate_report_title(self, report_date: str) -> str:
        """
        根據報告日期生成標準化的報告標題
        
        Args:
            report_date: 報告日期
            
        Returns:
            生成的報告標題
        """
        formatted_date = self.format_date_for_display(report_date)
        return f"🌈✨ 幼幼班主日學週報 - {formatted_date} 🧸🎈"
    
    def generate_report_content(self, content: str) -> Tuple[List[str], bool]:
        """
        生成報告內容
        
        Args:
            content: 原始內容
            
        Returns:
            Tuple[List[str], bool]: 報告內容段落列表和格式驗證狀態
        """
        # 使用 Gemini 生成報告
        report_text = self.gemini_service.generate_report(content)
        
        # 驗證並修復 Notion 格式兼容性
        is_valid, validated_report_text = self.format_validator_service.validate_notion_format(report_text)
        if not is_valid:
            logger.warning("Format validation failed, using original content")
        else:
            report_text = validated_report_text
            logger.info("Format validation successful")
        
        # 按段落分割
        report_content = report_text.split('\n\n')
        
        return report_content, is_valid
    
    def create_notion_page(self, report_date: str, report_content: List[str], image_paths: List[str]) -> Tuple[str, str]:
        """
        在 Notion 中創建報告頁面
        
        Args:
            report_date: 報告日期
            report_content: 報告內容段落列表
            image_paths: 圖片路徑列表
            
        Returns:
            Tuple[str, str]: 頁面 URL 和頁面 ID
        """
        # 生成標準化標題
        report_title = self.generate_report_title(report_date)
        
        # 創建 Notion 頁面
        page_url, page_id = self.notion_service.create_page(
            title=report_title,
            content=report_content,
            image_paths=image_paths,
            report_date=report_date
        )
        
        return page_url, page_id
    
    def generate_full_report(self, content: str, report_date: str, image_paths: List[str] = None) -> Dict[str, Any]:
        """
        生成完整報告並創建 Notion 頁面
        
        Args:
            content: 原始內容
            report_date: 報告日期
            image_paths: 圖片路徑列表
            
        Returns:
            Dict[str, Any]: 包含報告結果的字典
        """
        # 處理圖片路徑
        image_paths = image_paths or []
        
        # 生成報告內容
        report_content, is_valid = self.generate_report_content(content)
        
        # 創建 Notion 頁面
        page_url, page_id = self.create_notion_page(report_date, report_content, image_paths)
        
        # 返回結果
        return {
            "success": True,
            "notion_page_url": page_url,
            "notion_page_id": page_id,
            "report_content": report_content,
            "format_validation": is_valid
        } 
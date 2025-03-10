"""
報告生成服務 - 處理報告生成的核心業務邏輯
"""
import logging
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime

from utils.common.logging_utils import get_logger
from .interfaces import OutputPlatformInterface

logger = get_logger("report_service")

class ReportService:
    """處理報告生成的核心業務邏輯"""
    
    def __init__(self, gemini_service, output_platform: OutputPlatformInterface, format_validator_service):
        """
        初始化報告服務
        
        Args:
            gemini_service: Gemini AI 服務實例
            output_platform: 輸出平台實例
            format_validator_service: 格式驗證服務實例
        """
        self.gemini_service = gemini_service
        self.output_platform = output_platform
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
        
        # 驗證格式
        is_valid, validated_report_text = self.format_validator_service.validate_markdown_format(
            report_text,
        )
        
        if not is_valid:
            logger.warning("Format validation failed, using original content")
        else:
            report_text = validated_report_text
            logger.info("Format validation successful")
        
        # 按段落分割
        report_content = report_text.split('\n\n')
        
        return report_content, is_valid
    
    def generate_full_report(self, content: str, report_date: str, image_paths: List[str] = None) -> Dict[str, Any]:
        """
        生成完整報告並發布到指定平台
        
        Args:
            content: 原始內容
            report_date: 報告日期
            image_paths: 圖片路徑列表
            
        Returns:
            Dict[str, Any]: 包含報告結果的字典
        """
        # 處理圖片路徑
        image_paths = image_paths or []
        cloud_image_urls = []
        failed_images = []
        
        # 上傳圖片到雲端存儲
        if image_paths and hasattr(self.output_platform, 'storage_service'):
            storage_service = self.output_platform.storage_service
            for image_path in image_paths:
                if image_path:
                    cloud_url = storage_service.upload_image(image_path)
                    if cloud_url:
                        cloud_image_urls.append(cloud_url)
                        logger.info(f"Image uploaded successfully: {cloud_url}")
                    else:
                        failed_images.append(image_path)
                        logger.warning(f"Failed to upload image: {image_path}")
        
        # 如果有圖片上傳失敗，記錄警告
        if failed_images:
            logger.warning(f"Failed to upload {len(failed_images)} images: {failed_images}")
        
        # 生成報告內容
        report_content, is_valid = self.generate_report_content(content)
        
        # 生成標題
        report_title = self.generate_report_title(report_date)
        
        # 發布到指定平台，只使用成功上傳的圖片 URL
        result = self.output_platform.publish_report(
            title=report_title,
            content=report_content,
            report_date=report_date,
            image_paths=cloud_image_urls
        )
        
        # 返回結果
        return {
            "success": result["success"],
            "url": result["url"],
            "report_content": report_content,
            "format_validation": is_valid,
            "platform_data": result["platform_specific_data"],
            "failed_images": failed_images if failed_images else None
        } 
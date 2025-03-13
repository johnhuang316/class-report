"""
報告服務模組 - 處理報告生成和發布
"""
import logging
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime
from config import settings
import os
import re

from utils.common.logging_utils import get_logger
from services.gemini_service import GeminiService
from services.format_validator_service import FormatValidatorService
from .interfaces import OutputPlatformInterface

# 配置日誌
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
    
    def generate_report_title(self, report_date: str, user_title: str = "主日學週報") -> str:
        """
        根據報告日期和使用者提供的標題生成標準化的報告標題
        
        Args:
            report_date: 報告日期
            user_title: 使用者提供的標題，默認為"主日學週報"
            
        Returns:
            生成的報告標題
        """
        formatted_date = self.format_date_for_display(report_date)
        # 使用配置中的模板，填入使用者提供的標題和日期
        return settings.report_title_template.format(title=user_title, date=formatted_date)
    
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
    
    def generate_full_report(self, content: str, report_date: str, image_paths: List[str] = None, title: str = "主日學週報") -> Dict[str, Any]:
        """
        生成完整報告並發布到指定平台
        
        Args:
            content: 原始內容
            report_date: 報告日期
            image_paths: 圖片路徑列表
            title: 使用者提供的報告標題，默認為"主日學週報"
            
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
        report_title = self.generate_report_title(report_date, user_title=title)
        
        # 發布到指定平台，只使用成功上傳的圖片 URL
        result = self.output_platform.publish_report(
            title=report_title,
            content=report_content,
            report_date=report_date,
            image_paths=cloud_image_urls,
            original_content=content  # 傳遞原始內容
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
    
    def get_report_for_editing(self, report_path: str) -> Dict[str, Any]:
        """
        獲取報告內容用於編輯
        
        Args:
            report_path: 報告文件的路徑
            
        Returns:
            Dict[str, Any]: 包含報告內容的字典
        """
        from bs4 import BeautifulSoup
        
        # 檢查服務是否可用
        if not hasattr(self.output_platform, 'storage_service'):
            raise ValueError("Storage service is not available")
        
        # 獲取報告內容
        html_content = self.output_platform.storage_service.get_report_content(report_path)
        
        if not html_content:
            raise ValueError("Failed to get report content")
        
        # 從文件名中提取報告日期
        filename = report_path.split("/")[-1]
        report_date = filename.replace(".html", "")
        
        # 從 HTML 中提取原始 Markdown 內容
        # 使用 BeautifulSoup 解析 HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 查找包含原始 Markdown 的元素
        markdown_element = soup.find('div', id='original-markdown')
        
        if markdown_element and markdown_element.get('data-content'):
            # 從 data-content 屬性中獲取 Markdown 內容
            markdown_content = markdown_element['data-content']
            logger.info("Successfully extracted original Markdown content")
        else:
            # 如果找不到原始 Markdown，則報錯
            raise ValueError("Original Markdown content not found in the report")
        
        # 提取報告標題
        title_element = soup.find('h1')
        report_title = title_element.text if title_element else "主日學報告"
        # 移除 HTML 標籤，但保留換行符號以便在表單中顯示
        report_title = report_title.replace('<br>', '\n').replace('</br>', '')
        
        return {
            "report_path": report_path,
            "report_date": report_date,
            "markdown_content": markdown_content,
            "report_title": report_title
        }
    
    def update_report(self, report_path: str, title: str, content: str) -> Dict[str, Any]:
        """
        更新報告內容
        
        Args:
            report_path: 報告文件的路徑
            title: 更新後的報告標題
            content: 更新後的報告內容 (Markdown 格式)
            
        Returns:
            Dict[str, Any]: 包含更新結果的字典
        """
        from bs4 import BeautifulSoup
        
        # 檢查服務是否可用
        if not hasattr(self.output_platform, 'storage_service'):
            raise ValueError("Storage service is not available")
        
        # 獲取原始 HTML 內容
        original_html = self.output_platform.storage_service.get_report_content(report_path)
        
        if not original_html:
            raise ValueError("Failed to get original report content")
        
        # 使用 BeautifulSoup 解析原始 HTML
        soup = BeautifulSoup(original_html, 'html.parser')
        
        # 處理標題中的換行符，將其轉換為 <br> 標籤
        title = title.replace('\n', '<br>')
        
        # 從原始 HTML 中獲取之前的 original_content
        original_content_container = soup.find('div', class_='original-content')
        original_content = original_content_container.text.strip() if original_content_container else None
        
        # 將 Markdown 內容轉換為段落列表
        content_paragraphs = content.split('\n\n')
        
        # 獲取圖片區域
        image_gallery = soup.find('div', class_='image-gallery')
        image_paths = []
        
        if image_gallery:
            # 提取圖片路徑
            img_tags = image_gallery.find_all('img')
            image_paths = [img.get('src') for img in img_tags if img.get('src')]
            logger.info(f"Found {len(image_paths)} images in the report")
        
        # 使用與創建報告時相同的方法生成 HTML 內容
        new_html_content = self.output_platform._generate_html_content(
            title, 
            content_paragraphs,
            image_paths,
            original_content 
        )
        
        # 使用原始文件名（不包含 .html 擴展名）
        filename = report_path.split("/")[-1].replace(".html", "")
        logger.info(f"Updating report with filename: {filename}")
        
        # 上傳更新後的 HTML 內容
        url = self.output_platform.storage_service.upload_html(new_html_content, filename)
        
        if not url:
            raise ValueError("Failed to upload updated HTML content")
        
        return {
            "success": True,
            "url": url
        }
    
    def delete_report(self, report_path: str) -> Dict[str, bool]:
        """
        刪除指定的報告
        
        Args:
            report_path: 報告文件的路徑
            
        Returns:
            Dict[str, bool]: 包含刪除結果的字典
        """
        # 檢查服務是否可用
        if not hasattr(self.output_platform, 'storage_service'):
            raise ValueError("Storage service is not available")
        
        # 刪除報告
        success = self.output_platform.storage_service.delete_report(report_path)
        
        if not success:
            raise ValueError("Failed to delete report")
        
        return {
            "success": True
        }
    
    def list_reports(self) -> List[Dict[str, Any]]:
        """
        獲取已生成的報告列表
        
        Returns:
            List[Dict[str, Any]]: 報告列表
        """
        # 檢查服務是否可用
        if not hasattr(self.output_platform, 'storage_service'):
            raise ValueError("Storage service is not available")
        
        # 獲取報告列表
        reports = self.output_platform.storage_service.list_reports()
        
        return reports 
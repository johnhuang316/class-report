"""
依賴注入模組 - 處理服務初始化和依賴注入
"""
import logging
from typing import Optional, Tuple, Dict, Any
from functools import lru_cache

from fastapi import Depends

from config import settings
from services.gemini_service import GeminiService
from services.notion_service import NotionService
from services.storage_service import StorageService
from services.format_validator_service import FormatValidatorService
from services.report_service import ReportService
from services.file_service import FileService
from services.platforms.notion_platform import NotionPlatform
from services.platforms.gcs_platform import GCSPlatform
from services.interfaces import OutputPlatformInterface
from utils.common.logging_utils import get_logger

# 配置日誌
logger = get_logger("dependencies")

class ServiceContainer:
    """服務容器類，負責管理所有服務實例"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        
    def get_or_create(self, service_key: str, factory_func) -> Any:
        """
        獲取或創建服務實例
        
        Args:
            service_key: 服務的唯一標識
            factory_func: 創建服務的工廠函數
            
        Returns:
            Any: 服務實例
        """
        if service_key not in self._services:
            self._services[service_key] = factory_func()
        return self._services[service_key]
    
    def clear(self):
        """清除所有服務實例"""
        self._services.clear()

# 創建全局服務容器實例
service_container = ServiceContainer()

def get_gemini_service() -> Optional[GeminiService]:
    """獲取 Gemini 服務實例"""
    def create_service():
        try:
            return GeminiService(api_key=settings.gemini_api_key)
        except Exception as e:
            logger.error(f"Failed to initialize Gemini service: {str(e)}")
            return None
    
    return service_container.get_or_create("gemini", create_service)

def get_notion_service() -> Optional[NotionService]:
    """獲取 Notion 服務實例"""
    def create_service():
        try:
            service = NotionService(api_key=settings.notion_api_key)
            service.database_id = settings.notion_database_id
            return service
        except Exception as e:
            logger.error(f"Failed to initialize Notion service: {str(e)}")
            return None
    
    return service_container.get_or_create("notion", create_service)

def get_format_validator_service() -> Optional[FormatValidatorService]:
    """獲取格式驗證服務實例"""
    def create_service():
        try:
            return FormatValidatorService(api_key=settings.gemini_api_key)
        except Exception as e:
            logger.error(f"Failed to initialize Format Validator service: {str(e)}")
            return None
    
    return service_container.get_or_create("format_validator", create_service)

def get_storage_service() -> Optional[StorageService]:
    """獲取存儲服務實例"""
    def create_service():
        try:
            return StorageService()
        except Exception as e:
            logger.warning(f"Failed to initialize Storage service: {str(e)}")
            logger.warning("Application will continue without GCS storage capabilities")
            return None
    
    return service_container.get_or_create("storage", create_service)

def get_file_service() -> Optional[FileService]:
    """獲取文件服務實例"""
    def create_service():
        try:
            return FileService()
        except Exception as e:
            logger.error(f"Failed to initialize File service: {str(e)}")
            return None
    
    return service_container.get_or_create("file", create_service)

def get_output_platform(
    notion_service: Optional[NotionService] = Depends(get_notion_service),
    storage_service: Optional[StorageService] = Depends(get_storage_service)
) -> Optional[OutputPlatformInterface]:
    """獲取輸出平台實例"""
    def create_platform():
        platform_type = str(settings.output_platform).lower()
        
        if platform_type == "notion" and notion_service:
            return NotionPlatform(notion_service)
        elif platform_type == "gcs" and storage_service:
            return GCSPlatform(storage_service)
        else:
            raise ValueError(f"Invalid or unavailable platform type: {platform_type}")
    
    return service_container.get_or_create("output_platform", create_platform)

def get_report_service(
    gemini_service: Optional[GeminiService] = Depends(get_gemini_service),
    output_platform: Optional[OutputPlatformInterface] = Depends(get_output_platform),
    format_validator_service: Optional[FormatValidatorService] = Depends(get_format_validator_service)
) -> Optional[ReportService]:
    """獲取報告服務實例"""
    def create_service():
        if not all([gemini_service, output_platform, format_validator_service]):
            logger.error("Required services for ReportService are not available")
            return None
            
        service = ReportService(
            gemini_service=gemini_service,
            output_platform=output_platform,
            format_validator_service=format_validator_service
        )
        logger.info("Report service initialized successfully")
        return service
    
    return service_container.get_or_create("report", create_service)

def get_all_services() -> Tuple[Optional[GeminiService], Optional[NotionService], Optional[FormatValidatorService], Optional[StorageService], Optional[ReportService], Optional[FileService]]:
    """獲取所有服務實例"""
    gemini_service = get_gemini_service()
    notion_service = get_notion_service()
    format_validator_service = get_format_validator_service()
    storage_service = get_storage_service()
    file_service = get_file_service()
    report_service = get_report_service(gemini_service, get_output_platform(notion_service, storage_service), format_validator_service)
    
    return gemini_service, notion_service, format_validator_service, storage_service, report_service, file_service 
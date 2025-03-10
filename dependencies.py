"""
依賴注入模組 - 處理服務初始化和依賴注入
"""
import logging
from typing import Optional, Tuple

from fastapi import Depends

from config import settings
from services.gemini_service import GeminiService
from services.notion_service import NotionService
from services.storage_service import StorageService
from services.format_validator_service import FormatValidatorService
from services.report_service import ReportService
from services.file_service import FileService
from utils.common.logging_utils import get_logger

# 配置日誌
logger = get_logger("dependencies")

# 服務實例緩存
_gemini_service: Optional[GeminiService] = None
_notion_service: Optional[NotionService] = None
_format_validator_service: Optional[FormatValidatorService] = None
_storage_service: Optional[StorageService] = None
_report_service: Optional[ReportService] = None
_file_service: Optional[FileService] = None

def get_gemini_service() -> Optional[GeminiService]:
    """
    獲取 Gemini 服務實例
    
    Returns:
        Optional[GeminiService]: Gemini 服務實例，如果初始化失敗則返回 None
    """
    global _gemini_service
    
    if _gemini_service is None:
        try:
            _gemini_service = GeminiService(settings.gemini_api_key)
            logger.info("Gemini service initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Gemini service: {str(e)}")
            _gemini_service = None
            
    return _gemini_service

def get_notion_service() -> Optional[NotionService]:
    """
    獲取 Notion 服務實例
    
    Returns:
        Optional[NotionService]: Notion 服務實例，如果初始化失敗則返回 None
    """
    global _notion_service
    
    if _notion_service is None:
        try:
            _notion_service = NotionService(settings.notion_api_key)
            logger.info("Notion service initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Notion service: {str(e)}")
            _notion_service = None
            
    return _notion_service

def get_format_validator_service() -> Optional[FormatValidatorService]:
    """
    獲取格式驗證服務實例
    
    Returns:
        Optional[FormatValidatorService]: 格式驗證服務實例，如果初始化失敗則返回 None
    """
    global _format_validator_service
    
    if _format_validator_service is None:
        try:
            _format_validator_service = FormatValidatorService(settings.gemini_api_key)
            logger.info("Format Validator service initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Format Validator service: {str(e)}")
            _format_validator_service = None
            
    return _format_validator_service

def get_storage_service() -> Optional[StorageService]:
    """
    獲取存儲服務實例
    
    Returns:
        Optional[StorageService]: 存儲服務實例，如果初始化失敗則返回 None
    """
    global _storage_service
    
    if _storage_service is None:
        try:
            _storage_service = StorageService()
            logger.info("Storage service initialized successfully")
        except Exception as e:
            logger.warning(f"Storage service initialization failed: {str(e)}")
            logger.warning("Application will continue without GCS storage capabilities")
            _storage_service = None
            
    return _storage_service

def get_file_service() -> FileService:
    """
    獲取文件服務實例
    
    Returns:
        FileService: 文件服務實例
    """
    global _file_service
    
    if _file_service is None:
        _file_service = FileService()
        logger.info("File service initialized successfully")
            
    return _file_service

def get_report_service(
    gemini_service: Optional[GeminiService] = Depends(get_gemini_service),
    notion_service: Optional[NotionService] = Depends(get_notion_service),
    format_validator_service: Optional[FormatValidatorService] = Depends(get_format_validator_service)
) -> Optional[ReportService]:
    """
    獲取報告服務實例
    
    Args:
        gemini_service: Gemini 服務實例
        notion_service: Notion 服務實例
        format_validator_service: 格式驗證服務實例
        
    Returns:
        Optional[ReportService]: 報告服務實例，如果依賴服務初始化失敗則返回 None
    """
    global _report_service
    
    # 檢查依賴服務是否可用
    if not gemini_service or not notion_service or not format_validator_service:
        logger.error("Required services for ReportService are not available")
        return None
    
    if _report_service is None:
        _report_service = ReportService(gemini_service, notion_service, format_validator_service)
        logger.info("Report service initialized successfully")
            
    return _report_service

def get_all_services() -> Tuple[Optional[GeminiService], Optional[NotionService], Optional[FormatValidatorService], Optional[StorageService], Optional[ReportService], FileService]:
    """
    獲取所有服務實例
    
    Returns:
        Tuple: 所有服務實例的元組
    """
    gemini_service = get_gemini_service()
    notion_service = get_notion_service()
    format_validator_service = get_format_validator_service()
    storage_service = get_storage_service()
    file_service = get_file_service()
    report_service = get_report_service(gemini_service, notion_service, format_validator_service)
    
    return gemini_service, notion_service, format_validator_service, storage_service, report_service, file_service 
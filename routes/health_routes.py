"""
健康檢查路由模組
"""
from fastapi import APIRouter, Depends

from config import settings
from dependencies import get_gemini_service, get_notion_service, get_format_validator_service, get_storage_service
from utils.common.logging_utils import get_logger

# 配置日誌
logger = get_logger("health_routes")

# 創建路由器
router = APIRouter()

@router.get("/health")
async def health_check():
    """
    健康檢查端點，用於監控應用程序狀態。
    返回有關應用程序及其依賴項的狀態信息。
    """
    logger.info("Health check requested")
    
    # 獲取服務實例
    gemini_service = get_gemini_service()
    notion_service = get_notion_service()
    format_validator_service = get_format_validator_service()
    storage_service = get_storage_service()
    
    # 檢查 API 密鑰是否已設置
    api_keys_status = settings.get_api_keys_status()
    
    # 檢查服務是否已初始化
    services_status = {
        "gemini_service": gemini_service is not None,
        "notion_service": notion_service is not None,
        "format_validator_service": format_validator_service is not None,
        "storage_service": storage_service is not None
    }
    
    # 整體狀態
    status = "healthy" if all(api_keys_status.values()) and all(services_status.values()) else "degraded"
    
    return {
        "status": status,
        "version": settings.app_version,
        "api_keys": api_keys_status,
        "services": services_status
    } 
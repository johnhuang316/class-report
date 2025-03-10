"""
報告路由模組 - 處理報告生成相關的端點
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from pydantic import BaseModel
from utils.common.logging_utils import get_logger
from dependencies import get_report_service

# 配置日誌
logger = get_logger("report_routes")

# 創建路由器
router = APIRouter()

# 定義 API 的請求模型
class ReportRequest(BaseModel):
    content: str
    image_paths: Optional[List[str]] = []
    report_date: Optional[str] = None

@router.post("/generate-report", response_class=JSONResponse)
async def generate_report_api(
    report_request: ReportRequest,
    report_service = Depends(get_report_service)
):
    """
    API 端點，用於從提供的數據生成報告。
    
    Args:
        report_request: 包含報告內容、圖片路徑和報告日期的請求
        report_service: 報告服務實例
        
    Returns:
        JSONResponse: 包含生成報告結果的 JSON 響應
        
    Raises:
        HTTPException: 如果服務不可用或生成報告時發生錯誤
    """
    logger.info(f"Received API request to generate report")
    
    try:
        # 檢查服務是否可用
        if not report_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
                detail="Required services are not available"
            )
            
        # 生成報告
        result = report_service.generate_full_report(
            content=report_request.content,
            report_date=report_request.report_date,
            image_paths=report_request.image_paths
        )
        
        # 返回結果
        return {
            "success": True,
            "page_url": result["url"],
            "report_content": result["report_content"]
        }
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Failed to generate report: {str(e)}"
        ) 
"""
Web 路由模組 - 處理 Web 界面相關的端點
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Request, Form, UploadFile, HTTPException, status, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from utils.common.logging_utils import get_logger
from dependencies import get_report_service, get_file_service
from services.report_service import ReportService
from services.file_service import FileService

# 配置日誌
logger = get_logger("web_routes")

# 創建路由器
router = APIRouter()

# 設置模板
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    根路徑，返回主頁面。
    
    Args:
        request: 請求對象
        
    Returns:
        HTMLResponse: 包含主頁面的 HTML 響應
    """
    return templates.TemplateResponse(
        "index.html", 
        {"request": request}
    )

@router.post("/submit-form", response_class=HTMLResponse)
async def submit_form(
    request: Request,
    background_tasks: BackgroundTasks,
    report_date: str = Form(...),
    content: str = Form(...),
    images: list[UploadFile] = None,
    report_service: Optional[ReportService] = Depends(get_report_service),
    file_service: FileService = Depends(get_file_service)
):
    """
    處理表單提交，生成報告並創建 Notion 頁面。
    
    Args:
        request: 請求對象
        background_tasks: 背景任務對象，用於清理臨時文件
        report_date: 報告日期
        content: 報告內容
        images: 上傳的圖片列表
        report_service: 報告服務實例
        file_service: 文件服務實例
        
    Returns:
        HTMLResponse: 包含結果頁面的 HTML 響應
        
    Raises:
        HTTPException: 如果服務不可用或處理表單時發生錯誤
    """
    logger.info("Form submission received")
    logger.info(f"Report date: {report_date}")
    logger.info(f"Content length: {len(content)} characters")
    logger.info(f"Number of uploaded images: {len(images) if images else 0}")
    
    # 檢查服務是否可用
    if not report_service:
        error_message = "Required services are not available"
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": error_message
            },
            status_code=503
        )
    
    # 初始化響應變量
    notion_page_url = ""
    report_title = report_service.generate_report_title(report_date)
    report_content = []
    notion_permission_note = "Note: Notion API does not support setting page permissions automatically. Please set the page to 'Visible to everyone in the workspace' manually in Notion."
    error_message = None
    temp_image_paths = []
    
    try:
        # 處理圖片
        if images:
            temp_image_paths = await file_service.save_multiple_files(images)
            logger.info(f"Saved {len(temp_image_paths)} temporary images")
        
        # 生成報告
        result = report_service.generate_full_report(
            content=content,
            report_date=report_date,
            image_paths=temp_image_paths
        )
        
        # 設置響應數據
        notion_page_url = result["notion_page_url"]
        report_content = result["report_content"]
        
        # 添加背景任務以清理臨時文件
        background_tasks.add_task(file_service.clean_up_files, temp_image_paths)
        
        logger.info(f"Successfully created Notion page: {notion_page_url}")
        
    except Exception as e:
        logger.error(f"Error processing form: {str(e)}")
        
        # 清理臨時文件
        file_service.clean_up_files(temp_image_paths)
        
        error_message = f"處理失敗: {str(e)}"
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": error_message
            },
            status_code=500
        )
        
    # 返回成功頁面
    return templates.TemplateResponse(
        "success.html",
        {
            "request": request,
            "notion_page_url": notion_page_url,
            "report_title": report_title,
            "report_content": report_content,
            "notion_permission_note": notion_permission_note
        }
    ) 
"""
Web 路由模組 - 處理 Web 界面相關的端點
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Request, Form, UploadFile, HTTPException, status, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import markdown
from bs4 import BeautifulSoup

from utils.common.logging_utils import get_logger
from dependencies import get_report_service, get_file_service
from services.report_service import ReportService
from services.file_service import FileService
from services.platforms.gcs_platform import GCSPlatform

# 配置日誌
logger = get_logger("web_routes")

# 創建路由器
router = APIRouter()

# 設置模板
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def root(
    request: Request,
    report_service: Optional[ReportService] = Depends(get_report_service)
):
    """
    根路徑，返回主頁面。
    
    Args:
        request: 請求對象
        report_service: 報告服務實例
        
    Returns:
        HTMLResponse: 包含主頁面的 HTML 響應
    """
    # 獲取已生成的報告列表
    reports = []
    if report_service:
        try:
            reports = report_service.list_reports()
        except Exception as e:
            logger.error(f"Failed to list reports: {str(e)}")
    
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request,
            "reports": reports
        }
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
    page_url = ""
    report_title = report_service.generate_report_title(report_date)
    report_content = []
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
        
        if not result["success"]:
            raise Exception(result.get("error", "Unknown error occurred"))
        
        # 設置響應數據
        page_url = result["url"]
        report_content = result["report_content"]
        
        # 添加背景任務以清理臨時文件
        background_tasks.add_task(file_service.clean_up_files, temp_image_paths)
        
        logger.info(f"Successfully created report page: {page_url}")
        
        # 返回成功頁面
        return templates.TemplateResponse(
            "success.html",
            {
                "request": request,
                "page_url": page_url,
                "report_title": report_title,
                "report_content": report_content,
                "permission_note": result.get("platform_specific_data", {}).get("workspace_access", "")
            }
        )
        
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

@router.get("/delete-report/{report_path:path}", response_class=HTMLResponse)
async def delete_report(
    request: Request,
    report_path: str,
    report_service: Optional[ReportService] = Depends(get_report_service)
):
    """
    刪除指定的報告
    
    Args:
        request: 請求對象
        report_path: 報告文件的路徑
        report_service: 報告服務實例
        
    Returns:
        RedirectResponse: 重定向到主頁面
    """
    logger.info(f"Deleting report: {report_path}")
    
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
    
    try:
        # 使用 report_service 刪除報告
        result = report_service.delete_report(report_path)
        
        if not result["success"]:
            raise Exception("Failed to delete report")
        
        logger.info(f"Successfully deleted report: {report_path}")
        
        # 重定向到主頁面
        return RedirectResponse(url="/", status_code=303)
        
    except Exception as e:
        logger.error(f"Error deleting report: {str(e)}")
        
        error_message = f"刪除失敗: {str(e)}"
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": error_message
            },
            status_code=500
        )

@router.get("/edit-report/{report_path:path}", response_class=HTMLResponse)
async def edit_report_form(
    request: Request,
    report_path: str,
    report_service: Optional[ReportService] = Depends(get_report_service)
):
    """
    顯示編輯報告的表單
    
    Args:
        request: 請求對象
        report_path: 報告文件的路徑
        report_service: 報告服務實例
        
    Returns:
        HTMLResponse: 包含編輯表單的 HTML 響應
    """
    logger.info(f"Editing report: {report_path}")
    
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
    
    try:
        # 使用 report_service 獲取報告編輯信息
        report_data = report_service.get_report_for_editing(report_path)
        
        # 返回編輯表單
        return templates.TemplateResponse(
            "edit.html",
            {
                "request": request,
                **report_data  # 展開報告數據
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting report for editing: {str(e)}")
        
        error_message = f"獲取報告失敗: {str(e)}"
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": error_message
            },
            status_code=500
        )

@router.post("/update-report/{report_path:path}", response_class=HTMLResponse)
async def update_report(
    request: Request,
    report_path: str,
    title: str = Form(...),
    content: str = Form(...),
    report_service: Optional[ReportService] = Depends(get_report_service)
):
    """
    更新報告內容
    
    Args:
        request: 請求對象
        report_path: 報告文件的路徑
        title: 更新後的報告標題
        content: 更新後的報告內容 (Markdown 格式)
        report_service: 報告服務實例
        
    Returns:
        RedirectResponse: 重定向到主頁面
    """
    logger.info(f"Updating report: {report_path}")
    
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
    
    # 檢查是否為 GCSPlatform
    if not isinstance(report_service.output_platform, GCSPlatform):
        error_message = "不支援的平台類型，目前只支援 GCS 平台的報告修改"
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": error_message
            },
            status_code=400
        )
    
    try:
        # 使用 report_service 更新報告
        result = report_service.update_report(report_path, title, content)
        
        if not result["success"]:
            raise Exception("Failed to update report")
        
        # 重定向到主頁面
        return RedirectResponse(url="/", status_code=303)
        
    except Exception as e:
        logger.error(f"Error updating report: {str(e)}")
        
        error_message = f"更新報告失敗: {str(e)}"
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": error_message
            },
            status_code=500
        ) 
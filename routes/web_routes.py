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
    if report_service and hasattr(report_service.output_platform, 'storage_service'):
        try:
            reports = report_service.output_platform.storage_service.list_reports()
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
    if not report_service or not hasattr(report_service.output_platform, 'storage_service'):
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
        # 刪除報告
        success = report_service.output_platform.storage_service.delete_report(report_path)
        
        if not success:
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
    if not report_service or not hasattr(report_service.output_platform, 'storage_service'):
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
        # 獲取報告內容
        html_content = report_service.output_platform.storage_service.get_report_content(report_path)
        
        if not html_content:
            raise Exception("Failed to get report content")
        
        # 從文件名中提取報告日期
        # 假設文件名格式為 "YYYY年MM月DD日.html"
        filename = report_path.split("/")[-1]
        report_date = filename.replace(".html", "")
        
        # 從 HTML 中提取原始 Markdown 內容
        try:
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
                raise Exception("Original Markdown content not found in the report")
                
        except Exception as e:
            logger.error(f"Error extracting Markdown content: {str(e)}")
            raise
        
        # 返回編輯表單
        return templates.TemplateResponse(
            "edit.html",
            {
                "request": request,
                "report_path": report_path,
                "report_date": report_date,
                "markdown_content": markdown_content
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
    content: str = Form(...),
    report_service: Optional[ReportService] = Depends(get_report_service)
):
    """
    更新報告內容
    
    Args:
        request: 請求對象
        report_path: 報告文件的路徑
        content: 更新後的報告內容 (Markdown 格式)
        report_service: 報告服務實例
        
    Returns:
        RedirectResponse: 重定向到主頁面
    """
    logger.info(f"Updating report: {report_path}")
    
    # 檢查服務是否可用
    if not report_service or not hasattr(report_service.output_platform, 'storage_service'):
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
        # 獲取原始 HTML 內容作為模板
        original_html = report_service.output_platform.storage_service.get_report_content(report_path)
        
        if not original_html:
            raise Exception("Failed to get original report content")
        
        # 將 Markdown 轉換為 HTML
        # 使用 Python-Markdown 將 Markdown 轉換為 HTML
        html_content = markdown.markdown(content, extensions=['extra', 'nl2br'])
        
        # 使用 BeautifulSoup 解析原始 HTML
        soup = BeautifulSoup(original_html, 'html.parser')
        
        # 找到主要內容區域
        main_content = soup.find('div', class_='content')
        
        if not main_content:
            raise Exception("Content area not found in the report")
            
        # 替換主要內容區域
        main_content.clear()
        new_content = BeautifulSoup(html_content, 'html.parser')
        main_content.append(new_content)
        
        # 更新原始 Markdown 內容
        markdown_element = soup.find('div', id='original-markdown')
        
        if not markdown_element:
            raise Exception("Original Markdown element not found in the report")
            
        # 更新 Markdown 內容
        markdown_element['data-content'] = content.replace('"', '&quot;')
        
        # 更新報告內容
        storage_service = report_service.output_platform.storage_service
        
        # 獲取文件名
        filename = report_path.split("/")[-1].replace(".html", "")
        
        # 上傳更新後的內容
        url = storage_service.upload_html(str(soup), filename)
        
        if not url:
            raise Exception("Failed to update report")
        
        logger.info(f"Successfully updated report: {report_path}")
        
        # 重定向到主頁面
        return RedirectResponse(url="/", status_code=303)
        
    except Exception as e:
        logger.error(f"Error updating report: {str(e)}")
        
        error_message = f"更新失敗: {str(e)}"
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": error_message
            },
            status_code=500
        ) 
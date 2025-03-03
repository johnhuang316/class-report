# Import standard libraries
import os
import uuid
import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
import shutil

# Import FastAPI and related libraries
from fastapi import FastAPI, Form, File, UploadFile, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Import our custom modules
from services.gemini_service import GeminiService
from services.notion_service import NotionService
from services.storage_service import StorageService
from services.format_validator_service import FormatValidatorService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("main")

# Load environment variables
from dotenv import load_dotenv
load_dotenv()  # This loads the variables from .env

# Get environment variables or set defaults
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Initialize FastAPI app
app = FastAPI(
    title="Sunday School Weekly Report Generator",
    description="Generate weekly reports for Sunday School",
    version="1.0.0"
)

# Setup static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize API clients
try:
    # Initialize logger
    logger.info("Application starting...")
    
    # Check if API keys are set
    if not GEMINI_API_KEY:
        logger.warning("Environment variable GEMINI_API_KEY is not set. Please set it in the .env file")
        
    if not NOTION_API_KEY:
        logger.warning("Environment variable NOTION_API_KEY is not set. Please set it in the .env file")
        
    if not NOTION_DATABASE_ID:
        logger.warning("Environment variable NOTION_DATABASE_ID is not set. Please set it in the .env file")
    
    if not GCS_BUCKET_NAME:
        logger.warning("Environment variable GCS_BUCKET_NAME is not set. Please set it in the .env file")
    
    # Initialize Gemini client
    gemini_client = GeminiService(GEMINI_API_KEY)
    logger.info("Gemini client initialized successfully")
    
    # Initialize Notion client with storage service handling inside
    notion_client = NotionService(NOTION_API_KEY)
    logger.info("Notion client initialized successfully")
    
    # Initialize Format Validator service
    format_validator = FormatValidatorService(GEMINI_API_KEY)
    logger.info("Format Validator service initialized successfully")
    
    # Initialize Storage client (optional)
    try:
        storage_client = StorageService()
        logger.info("Storage client initialized successfully")
    except Exception as storage_error:
        logger.warning(f"Storage client initialization failed: {str(storage_error)}")
        logger.warning("Application will continue without GCS storage capabilities")
        storage_client = None
    
except Exception as e:
    logger.error(f"Error during initialization: {str(e)}")
    logger.exception(e)

# Define request model for API
class ReportRequest(BaseModel):
    content: str
    image_paths: Optional[List[str]] = []
    report_date: Optional[str] = None

class SignedUrlRequest(BaseModel):
    file_name: str
    content_type: Optional[str] = None

# Health check endpoint for monitoring
@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring the application status.
    Returns status information about the application and its dependencies.
    """
    logger.info("Health check requested")
    
    # Check if all required API keys are set
    api_keys_status = {
        "gemini_api_key": bool(GEMINI_API_KEY),
        "notion_api_key": bool(NOTION_API_KEY),
        "notion_database_id": bool(NOTION_DATABASE_ID)
    }
    
    # Check if clients are initialized
    clients_status = {
        "gemini_client": "gemini_client" in globals(),
        "notion_client": "notion_client" in globals(),
        "storage_client": "storage_client" in globals()
    }
    
    # Overall status
    status = "healthy" if all(api_keys_status.values()) and all(clients_status.values()) else "degraded"
    
    return {
        "status": status,
        "version": "1.0.0",
        "api_keys": api_keys_status,
        "clients": clients_status
    }

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(
        "index.html", 
        {"request": request}
    )

@app.post("/generate-report", response_class=JSONResponse)
async def generate_report_api(report_request: ReportRequest):
    """
    API endpoint to generate a report from provided data.
    """
    logger.info(f"Received API request to generate report")
    
    try:
        # Generate content using Gemini
        report_text = gemini_client.generate_report(report_request.content)
        
        # Validate and fix Notion format compatibility
        is_valid, validated_report_text = format_validator.validate_notion_format(report_text)
        if not is_valid:
            logger.warning("Format validation failed, using original content")
        else:
            report_text = validated_report_text
            logger.info("Format validation successful")
        
        report_content = report_text.split('\n\n')  # Split by paragraphs
        
        # Process image paths if provided
        image_paths = report_request.image_paths or []
        
        # Create Notion page
        page_url, page_id = notion_client.create_page(
            title="Sunday School Weekly Report",
            content=report_content,
            image_paths=image_paths,
            report_date=report_request.report_date
        )
        
        # Return results
        return {
            "success": True,
            "notion_page_url": page_url,
            "report_content": report_content
        }
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")

@app.post("/get-signed-url", response_class=JSONResponse)
async def get_signed_url(request: SignedUrlRequest):
    """
    獲取用於直接上傳到 GCS 的簽名 URL
    
    Args:
        request: 包含文件名和內容類型的請求
        
    Returns:
        包含簽名 URL 和其他信息的 JSON 響應
    """
    logger.info(f"Received request for signed URL: {request.file_name}")
    
    try:
        # 檢查 storage_service 是否可用
        if not storage_client:
            logger.error("Storage service is not available")
            raise HTTPException(status_code=500, detail="Storage service is not available")
        
        # 生成簽名 URL
        signed_url = storage_client.generate_signed_url(
            file_name=request.file_name,
            content_type=request.content_type
        )
        
        return {
            "success": True,
            "signed_url": signed_url,
            "file_name": request.file_name
        }
        
    except Exception as e:
        logger.error(f"Error generating signed URL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate signed URL: {str(e)}")

async def save_upload_file(upload_file: UploadFile) -> str:
    """
    保存上傳的文件到臨時位置
    
    Args:
        upload_file: 上傳的文件
        
    Returns:
        臨時文件路徑
        
    Note:
        文件會暫時保存在本地，上傳到 GCS 後會被刪除
    """
    if not upload_file.filename:
        return None
        
    # Create a unique filename to avoid conflicts
    file_extension = Path(upload_file.filename).suffix
    unique_filename = f"temp_{uuid.uuid4()}{file_extension}"
    
    # 使用絕對路徑保存臨時檔案
    temp_dir = os.path.join(os.getcwd(), "temp")
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, unique_filename)
    
    # Save the file
    with open(file_path, "wb") as buffer:
        buffer.write(upload_file.file.read())
        
    logger.info(f"Saved temporary file: {file_path}")
    return file_path

@app.post("/submit-form", response_class=HTMLResponse)
async def submit_form(
    request: Request,
    report_date: str = Form(...),
    content: str = Form(...),
    images: list[UploadFile] = None,
):
    logger.info("Form submission received")
    logger.info(f"Report date: {report_date}")
    logger.info(f"Content length: {len(content)} characters")
    logger.info(f"Number of uploaded images: {len(images) if images else 0}")
    
    # Initialize response variables
    notion_page_url = ""
    report_title = "Sunday School Weekly Report"
    report_content = []
    notion_permission_note = "Note: Notion API does not support setting page permissions automatically. Please set the page to 'Visible to everyone in the workspace' manually in Notion."
    error_message = None
    temp_image_paths = []
    
    try:
        # Generate content using Gemini
        report_text = gemini_client.generate_report(content)
        
        # Validate and fix Notion format compatibility
        is_valid, validated_report_text = format_validator.validate_notion_format(report_text)
        if not is_valid:
            logger.warning("Format validation failed, using original content")
        else:
            report_text = validated_report_text
            logger.info("Format validation successful")
        
        report_content = report_text.split('\n\n')  # Split by paragraphs
        
        # Process images
        if images:
            for img in images:
                if img.filename:
                    # Save uploaded images temporarily
                    temp_path = await save_upload_file(img)
                    if temp_path:  # 確保路徑有效
                        temp_image_paths.append(temp_path)
                        logger.info(f"Image temporarily saved: {temp_path}")
        
        # Create Notion page
        page_url, page_id = notion_client.create_page(
            title=report_title,
            content=report_content,
            image_paths=temp_image_paths,
            report_date=report_date  # Pass the report date to the Notion service
        )
        
        # 刪除本地臨時文件，因為圖片已經上傳到 GCS
        for path in temp_image_paths:
            if os.path.exists(path):
                try:
                    os.remove(path)
                    logger.info(f"Deleted local file after uploading to GCS: {path}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to delete local file: {path}, error: {str(cleanup_error)}")
        
        notion_page_url = page_url
        logger.info(f"Successfully created Notion page: {notion_page_url}")
        
        # Try to set page permissions to public
        # Note: This feature may not work because Notion API doesn't support setting page permissions
        try:
            notion_client.set_page_public_permissions(page_id)
        except Exception as e:
            logger.warning(f"Failed to set page permissions (expected): {str(e)}")
        
    except Exception as e:
        logger.error(f"Error processing form: {str(e)}")
        logger.exception(e)
        
        # 清理臨時文件，即使在發生錯誤的情況下
        for path in temp_image_paths:
            if os.path.exists(path):
                try:
                    os.remove(path)
                    logger.info(f"Cleaned up temporary file after error: {path}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up temporary file: {path}, error: {str(cleanup_error)}")
        
        error_message = f"處理失敗: {str(e)}"
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": error_message
            },
            status_code=500
        )
        
    # Return success page
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

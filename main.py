"""
主應用程序模組 - 初始化 FastAPI 應用程序並包含所有路由
"""
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# 導入配置和依賴
from config import settings
from dependencies import get_all_services
from routes import api_router
from utils.common.logging_utils import get_logger

# 配置日誌
logger = get_logger("main")

# 初始化 FastAPI 應用程序
app = FastAPI(**settings.get_fastapi_settings())

# 設置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://sundayhub.jumido.tw",
        "http://sundayhub.jumido.tw",
        "https://storage.googleapis.com"  # 如果通過 GCS 默認域名訪問
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # 只允許必要的 HTTP 方法
    allow_headers=["*"],
)

# 設置靜態文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 初始化服務
try:
    # 初始化日誌
    logger.info("Application starting...")
    
    # 檢查配置
    config_validation = settings.validate_settings()
    for key, value in config_validation.items():
        if not value:
            logger.warning(f"Environment variable {key.upper()} is not set. Please set it in the .env file")
    
    # 初始化所有服務
    gemini_service, notion_service, format_validator_service, storage_service, report_service, file_service = get_all_services()
    
    # 檢查關鍵服務是否可用
    if not gemini_service:
        logger.error("Gemini service initialization failed")
    if not notion_service:
        logger.error("Notion service initialization failed")
    if not report_service:
        logger.error("Report service initialization failed")
    
except Exception as e:
    logger.error(f"Error during initialization: {str(e)}")
    logger.exception(e)

# 包含所有路由
app.include_router(api_router)

# 啟動應用程序
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)

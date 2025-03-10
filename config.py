"""
配置管理模組 - 處理應用程序配置和環境變量
"""
import os
from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field

# 加載環境變量
from dotenv import load_dotenv
load_dotenv()  # 從 .env 文件加載變量

class AppSettings(BaseSettings):
    """應用程序配置設置"""
    
    # API 密鑰
    gemini_api_key: Optional[str] = Field(None, env="GEMINI_API_KEY")
    notion_api_key: Optional[str] = Field(None, env="NOTION_API_KEY")
    notion_database_id: Optional[str] = Field(None, env="NOTION_DATABASE_ID")
    
    # 存儲配置
    gcs_bucket_name: Optional[str] = Field(None, env="GCS_BUCKET_NAME")
    google_application_credentials: Optional[str] = Field(None, env="GOOGLE_APPLICATION_CREDENTIALS")
    
    # 應用程序配置
    app_name: str = "Sunday School Weekly Report Generator"
    app_description: str = "Generate weekly reports for Sunday School"
    app_version: str = "1.0.0"
    
    # 報告配置
    report_title_template: str = "🌈✨ 幼幼班主日學週報 - {date} 🧸🎈"
    
    # 服務器配置
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
    def validate_settings(self) -> Dict[str, bool]:
        """
        驗證配置設置
        
        Returns:
            Dict[str, bool]: 配置驗證結果
        """
        return {
            "gemini_api_key": bool(self.gemini_api_key),
            "notion_api_key": bool(self.notion_api_key),
            "notion_database_id": bool(self.notion_database_id),
            "gcs_bucket_name": bool(self.gcs_bucket_name),
            "google_application_credentials": bool(self.google_application_credentials)
        }
        
    def get_api_keys_status(self) -> Dict[str, bool]:
        """
        獲取 API 密鑰狀態
        
        Returns:
            Dict[str, bool]: API 密鑰狀態
        """
        return {
            "gemini_api_key": bool(self.gemini_api_key),
            "notion_api_key": bool(self.notion_api_key),
            "notion_database_id": bool(self.notion_database_id)
        }
        
    def get_fastapi_settings(self) -> Dict[str, Any]:
        """
        獲取 FastAPI 應用程序設置
        
        Returns:
            Dict[str, Any]: FastAPI 設置
        """
        return {
            "title": self.app_name,
            "description": self.app_description,
            "version": self.app_version
        }

# 創建全局設置實例
settings = AppSettings()

# 導出常用配置變量
GEMINI_API_KEY = settings.gemini_api_key
NOTION_API_KEY = settings.notion_api_key
NOTION_DATABASE_ID = settings.notion_database_id
GCS_BUCKET_NAME = settings.gcs_bucket_name
GOOGLE_APPLICATION_CREDENTIALS = settings.google_application_credentials 
"""
文件處理服務 - 處理文件上傳、保存和清理
"""
import os
import uuid
import logging
from pathlib import Path
from typing import List, Optional

from fastapi import UploadFile
from utils.common.logging_utils import get_logger

logger = get_logger("file_service")

class FileService:
    """處理文件上傳、保存和清理的服務"""
    
    def __init__(self, temp_dir: str = None):
        """
        初始化文件服務
        
        Args:
            temp_dir: 臨時文件目錄，默認為工作目錄下的 'temp'
        """
        self.temp_dir = temp_dir or os.path.join(os.getcwd(), "temp")
        os.makedirs(self.temp_dir, exist_ok=True)
        logger.info(f"File service initialized with temp directory: {self.temp_dir}")
    
    async def save_upload_file(self, upload_file: UploadFile) -> Optional[str]:
        """
        保存上傳的文件到臨時位置
        
        Args:
            upload_file: 上傳的文件
            
        Returns:
            Optional[str]: 臨時文件路徑，如果保存失敗則返回 None
            
        Note:
            文件會暫時保存在本地，上傳到雲存儲後應該被刪除
        """
        if not upload_file or not upload_file.filename:
            logger.warning("No file or filename provided")
            return None
            
        try:
            # 創建唯一文件名以避免衝突
            file_extension = Path(upload_file.filename).suffix
            unique_filename = f"temp_{uuid.uuid4()}{file_extension}"
            
            # 使用絕對路徑保存臨時檔案
            file_path = os.path.join(self.temp_dir, unique_filename)
            
            # 保存文件
            with open(file_path, "wb") as buffer:
                buffer.write(await upload_file.read())
                
            logger.info(f"Saved temporary file: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving uploaded file: {str(e)}")
            return None
    
    async def save_multiple_files(self, upload_files: List[UploadFile]) -> List[str]:
        """
        保存多個上傳的文件
        
        Args:
            upload_files: 上傳的文件列表
            
        Returns:
            List[str]: 成功保存的文件路徑列表
        """
        if not upload_files:
            return []
            
        saved_paths = []
        for file in upload_files:
            if file and file.filename:
                path = await self.save_upload_file(file)
                if path:
                    saved_paths.append(path)
                    
        return saved_paths
    
    def clean_up_files(self, file_paths: List[str]) -> None:
        """
        清理臨時文件
        
        Args:
            file_paths: 要清理的文件路徑列表
        """
        for path in file_paths:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                    logger.info(f"Deleted temporary file: {path}")
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file: {path}, error: {str(e)}")
    
    def clean_up_temp_directory(self) -> None:
        """清理整個臨時目錄"""
        try:
            for filename in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, filename)
                if os.path.isfile(file_path) and filename.startswith("temp_"):
                    os.remove(file_path)
                    logger.info(f"Cleaned up old temporary file: {file_path}")
        except Exception as e:
            logger.error(f"Error cleaning up temp directory: {str(e)}") 
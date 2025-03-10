"""
Notion 平台實現
"""
from typing import List, Dict, Any, Optional
from services.interfaces import OutputPlatformInterface
from utils.common.logging_utils import get_logger

logger = get_logger("notion_platform")

class NotionPlatform(OutputPlatformInterface):
    def __init__(self, notion_service):
        self.notion_service = notion_service
        self.storage_service = notion_service.storage_service
    
    def publish_report(
        self,
        title: str,
        content: List[str],
        report_date: str,
        image_paths: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        發布報告到 Notion
        
        Args:
            title: 報告標題
            content: 報告內容段落列表
            report_date: 報告日期
            image_paths: 圖片 URL 列表（已經上傳到雲端）
            
        Returns:
            Dict[str, Any]: 包含發布結果的字典
        """
        try:
            # 創建 Notion 頁面
            page_url, page_id = self.notion_service.create_page(
                title=title,
                content=content,
                image_paths=image_paths or [],
                report_date=report_date
            )
            
            return {
                "success": True,
                "url": page_url,
                "platform_specific_data": {
                    "page_id": page_id,
                    "workspace_access": "請手動設置頁面權限為「工作區所有人可見」"
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to publish to Notion: {str(e)}")
            return {
                "success": False,
                "url": "",
                "platform_specific_data": {
                    "error": str(e)
                }
            } 
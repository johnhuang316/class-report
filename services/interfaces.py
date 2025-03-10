"""
定義服務接口
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class OutputPlatformInterface(ABC):
    """輸出平台接口"""
    
    @abstractmethod
    def publish_report(
        self,
        title: str,
        content: List[str],
        report_date: str,
        image_paths: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        發布報告到指定平台
        
        Args:
            title: 報告標題
            content: 報告內容段落列表
            report_date: 報告日期
            image_paths: 圖片路徑列表
            
        Returns:
            Dict[str, Any]: 包含發布結果的字典，至少應該包含：
                - success: bool
                - url: str (發布後的訪問URL)
                - platform_specific_data: Dict[str, Any] (平台特定的返回數據)
        """
        pass 
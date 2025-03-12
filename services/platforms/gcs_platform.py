"""
Google Cloud Storage 靜態頁面平台實現
"""
from typing import List, Dict, Any, Optional
import markdown
from jinja2 import Environment, FileSystemLoader
from services.interfaces import OutputPlatformInterface
from utils.common.logging_utils import get_logger
from datetime import datetime
import re

logger = get_logger("gcs_platform")

class GCSPlatform(OutputPlatformInterface):
    def __init__(self, storage_service):
        self.storage_service = storage_service
        # 初始化 markdown 轉換器，啟用擴展功能
        self.markdown = markdown.Markdown(
            extensions=['extra', 'nl2br', 'sane_lists', 'smarty', 'tables']
        )
        # 初始化 Jinja2 環境
        self.jinja_env = Environment(
            loader=FileSystemLoader('templates'),
            autoescape=True
        )
        # 添加 nl2br 過濾器
        self.jinja_env.filters['nl2br'] = lambda value: value.replace('\n', '<br>') if value else ''
    
    def _convert_markdown_to_html(self, content: List[str]) -> str:
        """將 Markdown 內容轉換為 HTML"""
        try:
            # 合併內容並轉換
            markdown_text = "\n\n".join(content)
            
            # 處理 YouTube 連結，將其轉換為嵌入式影片
            # 匹配 [text](https://www.youtube.com/watch?v=VIDEO_ID) 或 [text](https://youtu.be/VIDEO_ID)
            youtube_pattern1 = r'\[([^\]]+)\]\((https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/))([a-zA-Z0-9_-]+)(?:[^\)]*?)\)'
            markdown_text = re.sub(youtube_pattern1, r'<div class="video-container"><iframe width="560" height="315" src="https://www.youtube.com/embed/\3" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe></div>', markdown_text)
            
            # 匹配純 URL: https://www.youtube.com/watch?v=VIDEO_ID 或 https://youtu.be/VIDEO_ID 或 https://www.youtube.com/shorts/VIDEO_ID
            youtube_pattern2 = r'(?<!\]\()(?<!\])\b(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/))([a-zA-Z0-9_-]+)(?:[^\s]*?)\b'
            markdown_text = re.sub(youtube_pattern2, r'<div class="video-container"><iframe width="560" height="315" src="https://www.youtube.com/embed/\2" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe></div>', markdown_text)
            
            html_content = self.markdown.convert(markdown_text)
            
            # 處理圖片標籤，確保圖片有響應式樣式
            html_content = html_content.replace('<img ', '<img style="max-width:100%; height:auto; display:block; margin:0 auto;" ')
            
            # 處理連結標籤，確保在新頁簽中打開
            html_content = html_content.replace('<a href', '<a target="_blank" rel="noopener noreferrer" href')
            
            # 添加 CSS 樣式以確保影片容器響應式
            html_content = html_content + """
            <style>
            .video-container {
                position: relative;
                padding-bottom: 56.25%; /* 16:9 比例 */
                height: 0;
                overflow: hidden;
                max-width: 100%;
                margin: 20px 0;
            }
            .video-container iframe {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
            }
            </style>
            """
            
            return html_content
        except Exception as e:
            logger.error(f"Markdown 轉換失敗: {str(e)}")
            # 返回簡單的 HTML 格式化，作為備用方案
            return "<p>" + "</p><p>".join([p.replace('\n', '<br>') for p in content]) + "</p>"
    
    def _generate_html_content(
        self,
        title: str,
        content: List[str],
        image_paths: Optional[List[str]] = None,
        original_content: Optional[str] = None
    ) -> str:
        """生成 HTML 內容"""
        # 轉換 Markdown 內容為 HTML
        content_html = self._convert_markdown_to_html(content)
        
        # 保存原始 Markdown 內容，用於編輯
        original_markdown = "\n\n".join(content)
        # 處理引號，避免 HTML 屬性問題
        original_markdown = original_markdown.replace('"', '&quot;')
        
        # 生成圖片 HTML
        images_html = ""
        if image_paths:
            images_html = "\n".join([
                f'<figure><img src="{img}" alt="主日學活動照片" loading="lazy" onerror="this.onerror=null; this.src=\'data:image/svg+xml;charset=utf-8,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 300 200%22%3E%3Crect width=%22300%22 height=%22200%22 fill=%22%23cccccc%22%3E%3C/rect%3E%3Ctext x=%22150%22 y=%22100%22 fill=%22%23ffffff%22 font-size=%2220%22 text-anchor=%22middle%22 alignment-baseline=%22middle%22%3E圖片載入失敗%3C/text%3E%3C/svg%3E\'"></figure>'
                for img in image_paths if img
            ])
        
        # 渲染模板
        template = self.jinja_env.get_template('reports/report_template.html')
        return template.render(
            title=title,
            content_html=content_html,
            images_html=images_html,
            original_content=original_content,
            original_markdown=original_markdown
        )
    
    def publish_report(
        self,
        title: str,
        content: List[str],
        report_date: str,
        image_paths: Optional[List[str]] = None,
        original_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        發布報告到 GCS 作為靜態頁面
        
        Args:
            title: 報告標題
            content: 報告內容段落列表
            report_date: 報告日期
            image_paths: 圖片 URL 列表（已經上傳到雲端）
            original_content: 用戶輸入的原始內容
            
        Returns:
            Dict[str, Any]: 包含發布結果的字典
        """
        try:
            # 生成 HTML 內容
            html_content = self._generate_html_content(
                title=title, 
                content=content, 
                image_paths=image_paths,
                original_content=original_content
            )
            
            # 生成帶時間戳的文件名
            timestamp = datetime.now().strftime("%H%M%S")
            filename = f"{title}_{timestamp}"
            
            # 上傳到 GCS
            page_url = self.storage_service.upload_html(html_content, filename)
            
            if not page_url:
                raise Exception("Failed to upload HTML to GCS")
            
            return {
                "success": True,
                "url": page_url,
                "platform_specific_data": {
                    "storage_path": f"sunday_school_reports/reports/{filename}.html"
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to publish to GCS: {str(e)}")
            return {
                "success": False,
                "url": "",
                "platform_specific_data": {
                    "error": str(e)
                }
            } 
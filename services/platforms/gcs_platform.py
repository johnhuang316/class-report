"""
Google Cloud Storage 靜態頁面平台實現
"""
from typing import List, Dict, Any, Optional
import markdown
from services.interfaces import OutputPlatformInterface
from utils.common.logging_utils import get_logger
from datetime import datetime

logger = get_logger("gcs_platform")

class GCSPlatform(OutputPlatformInterface):
    def __init__(self, storage_service):
        self.storage_service = storage_service
        # 初始化 markdown 轉換器，啟用擴展功能
        self.markdown = markdown.Markdown(
            extensions=['extra', 'nl2br', 'sane_lists', 'smarty', 'tables']
        )
    
    def _convert_markdown_to_html(self, content: List[str]) -> str:
        """將 Markdown 內容轉換為 HTML"""
        # 合併內容並轉換
        markdown_text = "\n\n".join(content)
        return self.markdown.convert(markdown_text)
    
    def _generate_html_content(
        self,
        title: str,
        content: List[str],
        image_paths: Optional[List[str]] = None
    ) -> str:
        """生成 HTML 內容"""
        # 轉換 Markdown 內容為 HTML
        content_html = self._convert_markdown_to_html(content)
        
        # 生成圖片 HTML
        images_section = ""
        if image_paths:
            images_html = "\n".join([
                f'<figure><img src="{img}" alt="主日學活動照片" loading="lazy"></figure>'
                for img in image_paths if img
            ])
            images_section = f'''
            <div class="image-gallery">
                <h2>📸 今日活動花絮 ✨</h2>
                {images_html}
            </div>
            '''
        
        return f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'Noto Sans TC', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.8;
            color: #4a4a4a;
            margin: 0;
            padding: 20px;
            background-color: #fef6e6;
            background-image: 
                radial-gradient(#ffd1d1 2px, transparent 2px),
                radial-gradient(#ffd1d1 2px, transparent 2px);
            background-size: 40px 40px;
            background-position: 0 0, 20px 20px;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background-color: rgba(255, 255, 255, 0.95);
            border-radius: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            padding: 40px;
            border: 8px solid #ffd166;
        }}
        h1 {{
            color: #ff6b6b;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 0 #ffd166;
            letter-spacing: 2px;
        }}
        .content {{
            background-color: white;
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
            border: 3px dashed #4ecdc4;
            margin-bottom: 30px;
        }}
        .image-gallery {{
            margin-top: 40px;
            padding: 30px;
            background-color: white;
            border-radius: 20px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
            border: 3px dashed #ff9f1c;
        }}
        .image-gallery h2 {{
            color: #ff9f1c;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2em;
            text-shadow: 1px 1px 0 #ffe66d;
        }}
        .image-gallery figure {{
            margin: 20px 0;
            padding: 15px;
            text-align: center;
            background-color: #fff9f0;
            border-radius: 15px;
            transition: transform 0.3s ease;
        }}
        .image-gallery figure:hover {{
            transform: translateY(-5px);
        }}
        .image-gallery img {{
            max-width: 100%;
            height: auto;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            margin-bottom: 15px;
            border: 5px solid white;
        }}
        .image-gallery figcaption {{
            color: #666;
            font-size: 1.1em;
            margin-top: 10px;
            font-weight: bold;
        }}
        blockquote {{
            border-left: 6px solid #4ecdc4;
            margin: 20px 0;
            padding: 20px;
            color: #2c3e50;
            background-color: #f8f9fa;
            border-radius: 0 15px 15px 0;
            font-size: 1.1em;
        }}
        .content h2 {{
            color: #ff6b6b;
            margin-top: 1.5em;
            padding-bottom: 0.5em;
            border-bottom: 3px dashed #ffd166;
            font-size: 1.8em;
        }}
        .content h3 {{
            color: #4ecdc4;
            margin-top: 1.2em;
            font-size: 1.5em;
        }}
        .content p {{
            margin: 1em 0;
            line-height: 2;
            font-size: 1.1em;
        }}
        .content strong {{
            color: #ff6b6b;
            font-weight: bold;
        }}
        .content ul, .content ol {{
            background-color: #fff9f0;
            padding: 20px 40px;
            border-radius: 15px;
            margin: 20px 0;
        }}
        .content li {{
            margin: 10px 0;
            line-height: 1.8;
            font-size: 1.1em;
        }}
        .content li::marker {{
            color: #ff6b6b;
            font-weight: bold;
        }}
        .emoji-divider {{
            text-align: center;
            font-size: 2em;
            margin: 30px 0;
            letter-spacing: 10px;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            color: #666;
            font-size: 0.9em;
        }}
        @media (max-width: 600px) {{
            body {{
                padding: 10px;
            }}
            .container {{
                padding: 20px;
            }}
            h1 {{
                font-size: 2em;
            }}
            .content {{
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        
        <div class="emoji-divider">
            🌈 ✨ 🎈 🧸 🎨
        </div>
        
        <div class="content">
            {content_html}
        </div>
        
        {images_section}
        
        <div class="emoji-divider">
            🙏 📖 ✝️ 🕊️ 💖
        </div>
        
        <div class="footer">
            <p>願神祝福每一位小朋友！</p>
        </div>
    </div>
</body>
</html>"""
    
    def publish_report(
        self,
        title: str,
        content: List[str],
        report_date: str,
        image_paths: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        發布報告到 GCS 作為靜態頁面
        
        Args:
            title: 報告標題
            content: 報告內容段落列表
            report_date: 報告日期
            image_paths: 圖片 URL 列表（已經上傳到雲端）
            
        Returns:
            Dict[str, Any]: 包含發布結果的字典
        """
        try:
            # 生成 HTML 內容
            html_content = self._generate_html_content(title, content, image_paths)
            
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
#!/usr/bin/env python3
"""
Test script for the Sunday School Weekly Report Generator.
This script tests the content generation functionality without requiring photo uploads.
It generates a report and posts it to a specified Notion database.

## 功能

- 從命令行參數或文本文件讀取課堂筆記內容
- 使用 Gemini AI 生成結構化的週報
- 驗證和修復 Markdown 內容的 Notion 格式兼容性
- 將生成的報告發布到指定的 Notion 數據庫
- 提供詳細的日誌輸出

## 前提條件

確保您已經設置了以下環境變數（可以在 `.env` 文件中設置）：

```
GEMINI_API_KEY=your_gemini_api_key
NOTION_API_KEY=your_notion_api_key
NOTION_DATABASE_ID=your_default_database_id
```

## 使用方法

### 基本用法

```bash
python test_report_generator.py --content-file sample_content.txt
```

### 直接提供內容

```bash
python test_report_generator.py --content "今天的主日學課程非常精彩！我們的主題是「耶穌愛小孩」..."
```

### 指定報告日期

```bash
python test_report_generator.py --content-file sample_content.txt --report-date 2025-03-06
```

### 發布到不同的 Notion 數據庫

```bash
python test_report_generator.py --content-file sample_content.txt --notion-database your_target_database_id
```

## 參數說明

- `--content`: 直接提供課堂筆記內容
- `--content-file`: 指定包含課堂筆記內容的文件路徑
- `--report-date`: 報告日期，格式為 YYYY-MM-DD（默認為今天）
- `--notion-database`: 目標 Notion 數據庫 ID（覆蓋環境變數中的設置）
- `--debug`: 啟用調試日誌

## 示例文件

已提供 `sample_content.txt` 作為示例輸入文件，您可以使用它來測試報告生成功能。
"""

import os
import argparse
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Import services from the main application
from services.gemini_service import GeminiService
from services.notion_service import NotionService
from services.format_validator_service import FormatValidatorService
from utils.common.logging_utils import get_logger

# Configure logging
logger = get_logger("test_report_generator")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test the Sunday School Weekly Report Generator")
    parser.add_argument("--content", type=str, help="Content to generate report from (classroom notes)")
    parser.add_argument("--content-file", type=str, help="Path to file containing content to generate report from")
    parser.add_argument("--report-date", type=str, help="Report date in YYYY-MM-DD format (default: today)")
    parser.add_argument("--notion-database", type=str, help="Target Notion database ID (overrides env variable)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()

def load_content_from_file(file_path: str) -> str:
    """Load content from a file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading content file: {str(e)}")
        raise

def initialize_services():
    """Initialize the required services."""
    # Load environment variables
    load_dotenv()
    
    # Get API keys from environment variables
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    notion_api_key = os.getenv("NOTION_API_KEY")
    
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")
    
    if not notion_api_key:
        raise ValueError("NOTION_API_KEY environment variable is not set")
    
    # Initialize services
    try:
        gemini_service = GeminiService(gemini_api_key)
        logger.info("Gemini service initialized successfully")
        
        notion_service = NotionService(notion_api_key)
        logger.info("Notion service initialized successfully")
        
        format_validator_service = FormatValidatorService(gemini_api_key)
        logger.info("Format validator service initialized successfully")
        
        return gemini_service, notion_service, format_validator_service
    except Exception as e:
        logger.error(f"Error initializing services: {str(e)}")
        raise

def generate_and_post_report(
    content: str,
    report_date: Optional[str],
    target_database_id: Optional[str],
    gemini_service: GeminiService,
    notion_service: NotionService,
    format_validator_service: FormatValidatorService
) -> Dict[str, Any]:
    """Generate a report and post it to Notion."""
    logger.info("Generating report from content")
    logger.info(f"Content length: {len(content)} characters")
    
    # Store original database ID before any operations
    original_database_id = os.environ.get("NOTION_DATABASE_ID")
    
    # Set a flag to track if we've modified the database ID
    database_id_modified = False
    
    try:
        # Generate content using Gemini
        report_text = gemini_service.generate_report(content)
        logger.info(f"Generated report length: {len(report_text)} characters")
        
        # Validate and fix Notion format compatibility
        is_valid, validated_report_text = format_validator_service.validate_notion_format(report_text)
        if not is_valid:
            logger.warning("Format validation failed, using original content")
        else:
            report_text = validated_report_text
            logger.info("Format validation successful")
        
        # Split content into paragraphs
        report_content = report_text.split('\n\n')
        
        # Override the database ID if provided
        if target_database_id:
            os.environ["NOTION_DATABASE_ID"] = target_database_id
            database_id_modified = True
            logger.info(f"Using target Notion database: {target_database_id}")
        
        # Create Notion page
        page_url, page_id = notion_service.create_page(
            title="Sunday School Weekly Report (Test)",
            content=report_content,
            image_paths=[],  # No images in test
            report_date=report_date
        )
        
        logger.info(f"Created Notion page: {page_url}")
        
        return {
            "success": True,
            "notion_page_url": page_url,
            "notion_page_id": page_id,
            "report_content": report_content
        }
    except Exception as e:
        logger.error(f"Error generating and posting report: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        # Restore original database ID if it was overridden
        if database_id_modified and original_database_id:
            os.environ["NOTION_DATABASE_ID"] = original_database_id
            logger.debug("Restored original Notion database ID")

def main():
    """Main function."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Configure logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Get content from arguments or file
    content = None
    if args.content:
        content = args.content
    elif args.content_file:
        content = load_content_from_file(args.content_file)
    else:
        logger.error("No content provided. Use --content or --content-file")
        return 1
    
    # Get report date (default to today)
    report_date = args.report_date
    if not report_date:
        report_date = datetime.now().strftime("%Y-%m-%d")
    
    # Initialize services
    try:
        gemini_service, notion_service, format_validator_service = initialize_services()
    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}")
        return 1
    
    # Generate and post report
    result = generate_and_post_report(
        content=content,
        report_date=report_date,
        target_database_id=args.notion_database,
        gemini_service=gemini_service,
        notion_service=notion_service,
        format_validator_service=format_validator_service
    )
    
    # Print result
    if result["success"]:
        logger.info("Report generated and posted successfully")
        logger.info(f"Notion page URL: {result['notion_page_url']}")
        
        # Print first few paragraphs of the report
        logger.info("Report preview:")
        for i, paragraph in enumerate(result["report_content"][:3]):
            logger.info(f"Paragraph {i+1}: {paragraph[:100]}...")
        
        if len(result["report_content"]) > 3:
            logger.info(f"... and {len(result['report_content']) - 3} more paragraphs")
    else:
        logger.error(f"Failed to generate and post report: {result['error']}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)

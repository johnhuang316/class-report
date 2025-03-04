import os
import logging
from dotenv import load_dotenv
from services.format_validator_service import FormatValidatorService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def test_format_validator():
    """Test the format validator service with a sample markdown content"""
    
    # Sample markdown with potential Notion compatibility issues
    test_content = """
# 主日學週報 📚✨

本週我們學習了**挪亞方舟**的故事。孩子們非常投入，尤其是在製作小動物模型的時候。

## 聖經故事 📖

> 「耶和華見人在地上罪惡很大，終日所思想的盡都是惡。」- 創世記 6:5

神命令挪亞建造一艘大船，因為他要用洪水消滅地上所有的生物。挪亞和他的家人，以及每種動物各取一對，都進入了方舟。

### 這是一個不被 Notion 支持的三級標題

表格測試（Notion 不支持）：
| 動物 | 數量 |
|------|------|
| 獅子 | 2    |
| 大象 | 2    |

---

## 活動回顧 🎨

孩子們參與了以下活動：
* 製作紙船模型 🚢
* 畫出最喜歡的動物 🦁
* 唱詩歌《神的應許》 🎵

<div>這是一個 HTML 標籤，Notion 不支持</div>

## 下週預告 📅

下週我們將學習**亞伯拉罕的故事**，請家長們提前與孩子們討論信心的重要性。

💖 感謝您關注我們的主日學活動！💖
    """
    
    try:
        # Initialize the format validator service
        validator = FormatValidatorService(GEMINI_API_KEY)
        
        # Validate the test content
        is_valid, fixed_content = validator.validate_notion_format(test_content)
        
        # Print results
        print("\n=== Original Content ===")
        print(test_content)
        print("\n=== Fixed Content ===")
        print(fixed_content)
        print("\n=== Validation Result ===")
        print(f"Is valid: {is_valid}")
        print(f"Changes made: {test_content != fixed_content}")
        
        return is_valid, fixed_content
        
    except Exception as e:
        logger.error(f"Error testing format validator: {str(e)}")
        return False, None

if __name__ == "__main__":
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY environment variable is not set. Please set it in the .env file")
    else:
        test_format_validator()

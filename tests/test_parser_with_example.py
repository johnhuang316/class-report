import os
import logging
from dotenv import load_dotenv
from utils.markdown.parser import MarkdownParser
from services.notion_service import NotionService
from utils.common.logging_utils import get_logger

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = get_logger(__name__)

# Load environment variables
load_dotenv()

# Get API key
NOTION_API_KEY = os.getenv("NOTION_API_KEY")

def test_parser_with_example():
    """Test the parser with the example article and upload to Notion"""
    
    # Example article provided by the user
    example_content = [
        "哈囉～各位親愛的家長和小寶貝們！🥰 這是來自幼兒部主日學的溫馨週報，讓我們一起回顧上週日（2/23）精彩又充滿愛的活動吧！💖",
        "# 💖 幼兒部主日學週報 (2025/02/23)",
        "## 🎵 音樂時光",
        "上週日，我們用滿滿的活力開始了我們的主日學！由凱碩老師和天智老師帶領，小寶貝們隨著音樂的節奏搖擺，一起唱跳了本月的主打歌曲〈我 主是答案〉！這首詩歌讓我們的心都向神敞開，感受到祂滿滿的愛與帶領。🎶",
        "## 👑 本週主題：珍貴的想法",
        "> 好的想法就像寶物一樣珍貴喔！💎",
        "本週我們一起學習了非常重要的真理，每一個從神而來的好的想 法，都如同寶物一樣，可以為我們帶來喜樂與祝福，我們應該要好好珍惜、實踐！",
        "---",
        "## 🤸‍♂️ 課後活動回顧：感統挑戰樂趣多！",
        "上週日的感統課真是太棒了！🤩 天智老師分享了讓孩子們在活動中進步  、建立自信的兩個關鍵，非常值得我們學習：",
        "-   **恰到好處的挑戰**：\n    活動設計不能太難，也不能太簡單。要讓孩子們在經過幾次嘗試與練習後，能夠成功完成任務。這樣他們會從中了解自己的能力，並學習 找方法進步。當孩子找到訣竅時，就會自然而然地產生自信，這種自信來自於自我成就，而不是他人的評價。我們只需在旁適度回應和鼓勵就可以囉！❤️",
        "-   **重複練習的重要性**：\n    神經連結需要透過不斷重複  來加強。💪 重複走同樣的路線、完成一樣的任務，每次進行微調，就能看見明顯的進步。",
        "天智老師觀察到，每個孩子的平衡能力、腳踝控制和手眼協調都有了顯著的進步！🎉 不僅比上一堂課進步，在當天課程前後的 表現也有明顯不同。當孩子們感受到自己對身體的掌控感提升時，都發自內心地感到喜悅呢！😊",
        "天智老師也特別鼓勵家長們，在家也可以和孩子們一起進行類似的活動。透過持續練習，您會發現孩子們不斷進步，同時 也能更了解孩子需要加強的部分。👨‍👩‍👧‍👦",
        "---",
        "期待下週與您和寶貝們再次相見！😇"
    ]
    
    try:
        # Initialize the parser
        parser = MarkdownParser()
        
        # Process the content
        blocks = parser.process_content(example_content)
        
        # Print the number of blocks generated
        logger.info(f"Generated {len(blocks)} blocks")
        
        # Print the types of blocks
        block_types = [block.get("type") for block in blocks]
        logger.info(f"Block types: {block_types}")
        
        # Check if we should upload to Notion
        if NOTION_API_KEY:
            # Initialize the Notion service
            notion_service = NotionService(NOTION_API_KEY)
            
            # Create a page with the parsed content
            page_url, page_id = notion_service.create_page(
                title="測試週報 - 幼兒部主日學週報 (2025/02/23)",
                content=example_content,
                report_date="2025-02-23"
            )
            
            logger.info(f"Created Notion page: {page_url}")
            logger.info(f"Page ID: {page_id}")
            
            print("\n=== Notion Upload Result ===")
            print(f"Page URL: {page_url}")
            print(f"Page ID: {page_id}")
            
            return page_url, page_id
        else:
            logger.warning("NOTION_API_KEY not set, skipping Notion upload")
            
            # Just print some of the blocks for inspection
            print("\n=== Parser Result (Sample) ===")
            for i, block in enumerate(blocks[:5]):  # Print first 5 blocks
                print(f"\nBlock {i+1} type: {block.get('type')}")
                print(f"Content: {block}")
            
            return None, None
        
    except Exception as e:
        logger.error(f"Error testing parser: {str(e)}")
        return None, None

if __name__ == "__main__":
    if not NOTION_API_KEY:
        logger.warning("NOTION_API_KEY environment variable is not set. Will run parser test only without Notion upload.")
    
    test_parser_with_example()

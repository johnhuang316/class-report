import json
import logging
from utils.markdown.parser import MarkdownParser
from utils.common.logging_utils import get_logger

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = get_logger(__name__)

def print_rich_text(rich_text):
    """Print rich_text objects for inspection"""
    for item in rich_text:
        content = item.get("text", {}).get("content", "")
        annotations = item.get("annotations", {})
        print(f"Content: '{content}'")
        if annotations:
            print(f"Annotations: {annotations}")
        print("---")

def test_list_item_with_bold_and_newline():
    """Test the parser's handling of list items with bold text and newlines"""
    
    parser = MarkdownParser()
    
    # Test cases focusing on the problematic list items
    test_cases = [
        "-   **恰到好處的挑戰**：\n    活動設計不能太難，也不能太簡單。要讓孩子們在經過幾次嘗試與練習後，能夠成功完成任務。",
        "-   **重複練習的重要性**：\n    神經連結需要透過不斷重複來加強。",
        "- **簡單測試**：沒有換行的內容",
        "- 普通列表項，沒有粗體和換行"
    ]
    
    print("=== 測試列表項中的粗體文本和換行 ===")
    
    for i, test_case in enumerate(test_cases):
        print(f"\n測試用例 {i+1}: '{test_case}'")
        
        # Convert the single line to a list for process_content
        content = [test_case]
        blocks = parser.process_content(content)
        
        print(f"生成了 {len(blocks)} 個區塊")
        
        # Print each block's type and structure
        for j, block in enumerate(blocks):
            block_type = block.get("type", "unknown")
            print(f"\n區塊 {j+1} 類型: {block_type}")
            
            if block_type == "bulleted_list_item":
                rich_text = block.get("bulleted_list_item", {}).get("rich_text", [])
                print("列表項內容:")
                print_rich_text(rich_text)
                
                # Check if there are children (indented content)
                children = block.get("bulleted_list_item", {}).get("children", [])
                if children:
                    print(f"子區塊數量: {len(children)}")
                    for k, child in enumerate(children):
                        child_type = child.get("type", "unknown")
                        print(f"  子區塊 {k+1} 類型: {child_type}")
                        
                        if child_type == "paragraph":
                            child_rich_text = child.get("paragraph", {}).get("rich_text", [])
                            print("  段落內容:")
                            for item in child_rich_text:
                                content = item.get("text", {}).get("content", "")
                                annotations = item.get("annotations", {})
                                print(f"    Content: '{content}'")
                                if annotations:
                                    print(f"    Annotations: {annotations}")
            else:
                print(f"非列表項區塊: {json.dumps(block, indent=2, ensure_ascii=False)}")

def test_full_example():
    """Test the parser with the full example article"""
    
    parser = MarkdownParser()
    
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
    
    print("\n=== 測試完整範例文章 ===")
    
    # Process the content
    blocks = parser.process_content(example_content)
    
    # Print the number of blocks generated
    print(f"生成了 {len(blocks)} 個區塊")
    
    # Print the types of blocks
    block_types = [block.get("type") for block in blocks]
    print(f"區塊類型: {block_types}")
    
    # Focus on the list items in the problematic section
    print("\n=== 重點檢查列表項區塊 ===")
    list_item_blocks = [block for block in blocks if block.get("type") == "bulleted_list_item"]
    
    for i, block in enumerate(list_item_blocks):
        print(f"\n列表項 {i+1}:")
        rich_text = block.get("bulleted_list_item", {}).get("rich_text", [])
        
        # Print the rich text content
        print("內容:")
        for j, item in enumerate(rich_text):
            content = item.get("text", {}).get("content", "")
            annotations = item.get("annotations", {})
            print(f"  項目 {j+1}: '{content}'")
            if annotations:
                print(f"  註釋: {annotations}")
        
        # Check if there are children (indented content)
        children = block.get("bulleted_list_item", {}).get("children", [])
        if children:
            print(f"子區塊數量: {len(children)}")
            for k, child in enumerate(children):
                child_type = child.get("type", "unknown")
                print(f"  子區塊 {k+1} 類型: {child_type}")
                
                if child_type == "paragraph":
                    child_rich_text = child.get("paragraph", {}).get("rich_text", [])
                    print("  段落內容:")
                    for item in child_rich_text:
                        content = item.get("text", {}).get("content", "")
                        print(f"    '{content}'")

if __name__ == "__main__":
    print("=== 開始測試 Markdown 解析器 ===")
    
    # Test individual list items
    test_list_item_with_bold_and_newline()
    
    # Test the full example
    test_full_example()
    
    print("\n=== 測試完成 ===")

"""
測試 Markdown 解析器對於帶有星號的文本的處理。
"""
import json
from utils.markdown.parser import MarkdownParser
import re

def print_rich_text(rich_text):
    """打印 rich_text 對象的內容，便於檢查"""
    for item in rich_text:
        content = item.get("text", {}).get("content", "")
        annotations = item.get("annotations", {})
        print(f"Content: '{content}'")
        if annotations:
            print(f"Annotations: {annotations}")
        print("---")

def test_asterisk_in_text():
    """測試文本中包含星號的情況"""
    parser = MarkdownParser()
    
    # 測試用例
    test_cases = [
        "1. **剛剛好的挑戰：** 活動設計不能太難，",
        "這是一個 *斜體* 文本",
        "這是一個 **粗體** 文本",
        "這是一個 ***粗斜體*** 文本",
        "這是一個普通文本中帶有星號 * 的例子",
        "這是一個帶有多個星號 * * * 的例子",
        "這是一個帶有未閉合星號 *的例子",
        "這是一個帶有未閉合雙星號 **的例子",
    ]
    
    print("=== 測試文本中包含星號的情況 ===")
    for i, test_case in enumerate(test_cases):
        print(f"\n測試用例 {i+1}: '{test_case}'")
        rich_text = parser.parse_line(test_case)
        print("解析結果:")
        print_rich_text(rich_text)
        
        # 檢查解析後的內容是否完整
        # 注意：我們不計算 Markdown 標記，只計算實際內容
        all_content = "".join(item.get("text", {}).get("content", "") for item in rich_text)
        
        # 移除原始文本中的 Markdown 標記以進行比較
        clean_original = test_case
        # 移除粗體和斜體標記
        clean_original = re.sub(r'\*\*\*(.*?)\*\*\*', r'\1', clean_original)  # ***text*** -> text
        clean_original = re.sub(r'\*\*(.*?)\*\*', r'\1', clean_original)      # **text** -> text
        clean_original = re.sub(r'(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)', r'\1', clean_original)  # *text* -> text
        # 移除連結標記
        clean_original = re.sub(r'\[(.*?)\]\((.*?)\)', r'\1', clean_original)  # [text](url) -> text
        
        if all_content.strip() != clean_original.strip():
            print(f"警告: 內容不匹配!")
            print(f"預期: '{clean_original.strip()}'")
            print(f"實際: '{all_content.strip()}'")
            
            # 找出差異
            import difflib
            diff = difflib.ndiff(clean_original.strip(), all_content.strip())
            print("差異:")
            print(''.join(diff))

def test_process_content():
    """測試整段內容的處理"""
    parser = MarkdownParser()
    
    # 測試用例
    content = [
        "# 測試標題",
        "",
        "1. **剛剛好的挑戰：** 活動設計不能太難，",
        "2. 這是第二點",
        "",
        "這是一個普通段落。",
        "",
        "---",
        "",
        "> 這是一個引用區塊",
        "> 這是引用區塊的第二行"
    ]
    
    print("\n=== 測試整段內容的處理 ===")
    blocks = parser.process_content(content)
    print(f"生成了 {len(blocks)} 個區塊")
    
    # 打印每個區塊的類型和內容
    for i, block in enumerate(blocks):
        block_type = block.get("type", "unknown")
        print(f"\n區塊 {i+1} 類型: {block_type}")
        
        if block_type == "paragraph":
            rich_text = block.get("paragraph", {}).get("rich_text", [])
            print("段落內容:")
            print_rich_text(rich_text)
        elif block_type == "heading_2":
            rich_text = block.get("heading_2", {}).get("rich_text", [])
            print("標題內容:")
            print_rich_text(rich_text)
        elif block_type == "bulleted_list_item":
            rich_text = block.get("bulleted_list_item", {}).get("rich_text", [])
            print("列表項內容:")
            print_rich_text(rich_text)
        elif block_type == "numbered_list_item":
            rich_text = block.get("numbered_list_item", {}).get("rich_text", [])
            print("數字列表項內容:")
            print_rich_text(rich_text)
        elif block_type == "divider":
            print("分隔線")
        elif block_type == "quote":
            rich_text = block.get("quote", {}).get("rich_text", [])
            print("引用區塊內容:")
            print_rich_text(rich_text)
        else:
            print(f"其他類型區塊: {json.dumps(block, indent=2, ensure_ascii=False)}")
    
    # 特別檢查引用區塊
    for block in blocks:
        if block.get("type") == "quote":
            print("\n詳細檢查引用區塊:")
            rich_text = block.get("quote", {}).get("rich_text", [])
            for i, item in enumerate(rich_text):
                print(f"項目 {i+1}:")
                print(f"  類型: {item.get('type')}")
                print(f"  內容: '{item.get('text', {}).get('content', '')}'")
                if item.get("annotations"):
                    print(f"  註釋: {item.get('annotations')}")
            
if __name__ == "__main__":
    # 只運行整段內容測試，以便查看所有區塊
    test_process_content() 
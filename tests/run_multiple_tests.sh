#!/bin/bash

echo "主日學週報生成器多報告測試工具"
echo "==========================="
echo

# 檢查是否有命令行參數
if [ $# -eq 0 ]; then
    echo "使用預設設置：範例內容生成3篇報告並發布到 Notion..."
    echo
    python test_multiple_reports.py
else
    echo "使用自定義設置運行測試..."
    echo
    python test_multiple_reports.py "$@"
fi

echo
echo "測試完成！"
echo
read -p "按 Enter 鍵繼續..." 
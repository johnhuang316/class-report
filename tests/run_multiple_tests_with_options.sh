#!/bin/bash

echo "主日學週報生成器多報告測試工具 - 進階選項"
echo "====================================="
echo

show_menu() {
    echo "請選擇要運行的測試選項："
    echo
    echo "1. 使用預設設置（範例內容生成3篇報告）"
    echo "2. 指定生成報告數量（5篇）"
    echo "3. 指定報告日期（2025-03-06）"
    echo "4. 使用自定義內容文件"
    echo "5. 啟用調試模式"
    echo "6. 自定義參數運行"
    echo "7. 退出"
    echo
}

while true; do
    show_menu
    read -p "請輸入選項（1-7）: " choice
    
    case $choice in
        1)
            echo
            echo "使用預設設置運行測試..."
            python test_multiple_reports.py
            break
            ;;
        2)
            echo
            echo "生成5篇報告..."
            python test_multiple_reports.py --num-reports 5
            break
            ;;
        3)
            echo
            echo "使用指定日期（2025-03-06）生成報告..."
            python test_multiple_reports.py --report-date 2025-03-06
            break
            ;;
        4)
            echo
            read -p "請輸入內容文件路徑: " content_file
            echo "使用文件 $content_file 生成報告..."
            python test_multiple_reports.py --content-file "$content_file"
            break
            ;;
        5)
            echo
            echo "啟用調試模式運行測試..."
            python test_multiple_reports.py --debug
            break
            ;;
        6)
            echo
            echo "可用參數說明："
            echo "--content \"直接輸入內容\""
            echo "--content-file 內容文件路徑"
            echo "--report-date YYYY-MM-DD"
            echo "--notion-database 數據庫ID"
            echo "--num-reports 報告數量"
            echo "--debug"
            echo
            read -p "請輸入參數: " params
            echo
            echo "使用自定義參數運行測試：$params"
            python test_multiple_reports.py $params
            break
            ;;
        7)
            echo
            echo "退出程序..."
            exit 0
            ;;
        *)
            echo
            echo "無效選項，請重新選擇。"
            echo
            ;;
    esac
done

echo
echo "測試完成！"
echo
read -p "按 Enter 鍵繼續..." 
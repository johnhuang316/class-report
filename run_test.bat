@echo off
echo Sunday School Weekly Report Generator Test Tool
echo ===========================
echo.
echo Generating report with sample content and publishing to Notion...
echo.
python test_report_generator.py --content-file sample_content.txt %*
echo.
echo To publish to a different Notion database, use:
echo run_test.bat --notion-database your_database_id
echo.
echo To specify report date, use:
echo run_test.bat --report-date YYYY-MM-DD
echo.
echo To enable debug logging, use:
echo run_test.bat --debug
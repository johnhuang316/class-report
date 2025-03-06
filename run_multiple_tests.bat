@echo off
echo Sunday School Weekly Report Generator - Multiple Reports Test
echo =========================================================
echo.

REM Check if command line arguments are provided
if "%~1"=="" (
    echo Using default settings: Generating 3 reports from sample content and posting to Notion...
    echo.
    python test_multiple_reports.py
) else (
    echo Running test with custom settings...
    echo.
    python test_multiple_reports.py %*
)

echo.
echo Test completed!
echo.
pause

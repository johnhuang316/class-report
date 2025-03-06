@echo off
echo Sunday School Weekly Report Generator - Advanced Options
echo ====================================================
echo.

:menu
echo Please select a test option:
echo.
echo 1. Use default settings (generate 3 reports from sample content)
echo 2. Specify number of reports (5 reports)
echo 3. Specify report date (2025-03-06)
echo 4. Use custom content file
echo 5. Enable debug mode
echo 6. Run with custom parameters
echo 7. Exit
echo.

set /p choice=Enter option (1-7): 

if "%choice%"=="1" (
    echo.
    echo Running test with default settings...
    python test_multiple_reports.py
    goto end
)

if "%choice%"=="2" (
    echo.
    echo Generating 5 reports...
    python test_multiple_reports.py --num-reports 5
    goto end
)

if "%choice%"=="3" (
    echo.
    echo Using specified date (2025-03-06) for reports...
    python test_multiple_reports.py --report-date 2025-03-06
    goto end
)

if "%choice%"=="4" (
    echo.
    set /p content_file=Enter content file path: 
    echo Using file %content_file% to generate reports...
    python test_multiple_reports.py --content-file "%content_file%"
    goto end
)

if "%choice%"=="5" (
    echo.
    echo Running test with debug mode enabled...
    python test_multiple_reports.py --debug
    goto end
)

if "%choice%"=="6" (
    echo.
    echo Available parameters:
    echo --content "Direct input content"
    echo --content-file path_to_content_file
    echo --report-date YYYY-MM-DD
    echo --notion-database database_id
    echo --num-reports number_of_reports
    echo --debug
    echo.
    set /p params=Enter parameters: 
    echo.
    echo Running test with custom parameters: %params%
    python test_multiple_reports.py %params%
    goto end
)

if "%choice%"=="7" (
    echo.
    echo Exiting program...
    goto exit
)

echo.
echo Invalid option, please try again.
echo.
goto menu

:end
echo.
echo Test completed!

:exit
echo.
pause 
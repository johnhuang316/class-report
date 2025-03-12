# Test Documentation for Sunday School Report Generator

This document provides an overview of all test files in the project, their purposes, and how to use them.

## Test Files Overview

| File Name | Type | Purpose |
|-----------|------|---------|
| `test_app.py` | Unit Tests | Tests the FastAPI application endpoints and error handling |
| `test_report_generator.py` | Integration Test | Tests the end-to-end report generation and publishing process |
| `test_multiple_reports.py` | Integration Test | Tests generating multiple reports from the same input |
| `test_format_validator.py` | Unit Test | Tests the format validation service for Markdown content |
| `test_markdown_parser.py` | Unit Test | Tests the Markdown parser's handling of special characters |
| `test_parser_list_items.py` | Unit Test | Tests the parser's handling of list items with formatting |
| `test_parser_with_example.py` | Integration Test | Tests the parser with a real-world example |

## Running Scripts

| File Name | Platform | Purpose |
|-----------|----------|---------|
| `run_test.sh` | Linux/Mac | Runs the basic report generation test |
| `run_test.bat` | Windows | Runs the basic report generation test |
| `run_multiple_tests.sh` | Linux/Mac | Runs the multiple reports test |
| `run_multiple_tests.bat` | Windows | Runs the multiple reports test |
| `run_multiple_tests_with_options.sh` | Linux/Mac | Runs the multiple reports test with various options |
| `run_multiple_tests_with_options.bat` | Windows | Runs the multiple reports test with various options |

## Detailed Test Descriptions

### Unit Tests

#### `test_app.py`

Tests the FastAPI application endpoints and error handling using pytest.

**Test Cases:**
- `test_health_endpoint`: Tests the health check endpoint
- `test_home_page`: Tests the home page rendering
- `test_generate_report_api`: Tests the report generation API endpoint
- `test_gemini_error_handling`: Tests error handling for Gemini API failures
- `test_submit_form`: Tests the form submission endpoint

**How to Run:**
```bash
pytest -v test_app.py
```

#### `test_format_validator.py`

Tests the format validation service that ensures Markdown content is compatible with the output platform.

**Test Cases:**
- `test_format_validator`: Tests validation and fixing of Markdown content with potential compatibility issues

**How to Run:**
```bash
python test_format_validator.py
```

#### `test_markdown_parser.py`

Tests the Markdown parser's handling of special characters and formatting.

**Test Cases:**
- `test_asterisk_in_text`: Tests handling of asterisks in text
- `test_process_content`: Tests processing of complete content

**How to Run:**
```bash
python test_markdown_parser.py
```

#### `test_parser_list_items.py`

Tests the parser's handling of list items with complex formatting.

**Test Cases:**
- `test_list_item_with_bold_and_newline`: Tests list items with bold text and newlines
- `test_full_example`: Tests a complete example with various list formats

**How to Run:**
```bash
python test_parser_list_items.py
```

### Integration Tests

#### `test_report_generator.py`

Tests the end-to-end report generation and publishing process.

**Features:**
- Reads content from command line or text file
- Generates structured reports using Gemini AI
- Validates and fixes Markdown format compatibility
- Publishes reports to a specified platform
- Provides detailed logging

**Command Line Options:**
- `--content`: Directly provide content text
- `--content-file`: Path to a file containing content
- `--report-date`: Specify the report date (YYYY-MM-DD)
- `--notion-database`: Specify a target Notion database ID
- `--debug`: Enable debug logging

**How to Run:**
```bash
python test_report_generator.py --content-file sample_content.txt
```

#### `test_multiple_reports.py`

Tests generating multiple reports from the same input to evaluate consistency.

**Features:**
- Generates multiple reports (default: 3) from the same input
- Compares the outputs for consistency
- Publishes all reports to the specified platform

**Command Line Options:**
- `--content`: Directly provide content text
- `--content-file`: Path to a file containing content
- `--report-date`: Specify the report date (YYYY-MM-DD)
- `--notion-database`: Specify a target Notion database ID
- `--num-reports`: Number of reports to generate (default: 3)
- `--debug`: Enable debug logging

**How to Run:**
```bash
python test_multiple_reports.py --content-file sample_content.txt --num-reports 5
```

#### `test_parser_with_example.py`

Tests the Markdown parser with a real-world example and optionally uploads to Notion.

**Features:**
- Tests parser with a realistic example
- Generates blocks for Notion
- Optionally uploads to Notion if API key is available

**How to Run:**
```bash
python test_parser_with_example.py
```

## Helper Scripts

### Basic Test Runners

#### `run_test.sh` / `run_test.bat`

Runs the basic report generation test with sample content.

**Options:**
- `--notion-database your_database_id`: Publish to a specific Notion database
- `--report-date YYYY-MM-DD`: Specify a report date
- `--debug`: Enable debug logging

**How to Run:**
```bash
# Linux/Mac
./run_test.sh

# Windows
run_test.bat
```

### Multiple Tests Runners

#### `run_multiple_tests.sh` / `run_multiple_tests.bat`

Runs the multiple reports test with default settings.

**How to Run:**
```bash
# Linux/Mac
./run_multiple_tests.sh

# Windows
run_multiple_tests.bat
```

#### `run_multiple_tests_with_options.sh` / `run_multiple_tests_with_options.bat`

Runs the multiple reports test with various predefined options.

**How to Run:**
```bash
# Linux/Mac
./run_multiple_tests_with_options.sh

# Windows
run_multiple_tests_with_options.bat
```

## Prerequisites

Before running tests, ensure you have set up the following environment variables in your `.env` file:

```
GEMINI_API_KEY=your_gemini_api_key
NOTION_API_KEY=your_notion_api_key
NOTION_DATABASE_ID=your_default_database_id
```

## Sample Content

The `sample_content.txt` file contains example content for testing. You can modify this file or create your own content files for testing.

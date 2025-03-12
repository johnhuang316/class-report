#!/usr/bin/env python3
"""
Unit tests for the Sunday School Weekly Report Generator.
"""

import os
import pytest
from fastapi.testclient import TestClient
import json
from unittest.mock import patch, MagicMock, AsyncMock

# Import the FastAPI app
from main import app

# Create a test client
client = TestClient(app)

def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "api_keys" in data
    assert "clients" in data

def test_home_page():
    """Test the home page."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Sunday School" in response.text
    assert "Generate Report" in response.text

@patch("main.notion_client.create_page", new_callable=AsyncMock)
@patch("main.gemini_client.generate_report", new_callable=AsyncMock)
def test_generate_report_api(mock_generate_report, mock_create_page):
    """Test the generate report API endpoint."""
    # Mock the Gemini and Notion client responses
    mock_generate_report.return_value = "Today was a wonderful day in Sunday School!\n\nWe learned about important Bible stories."
    mock_create_page.return_value = ("https://notion.so/new-page-id", "new-page-id")

    # Send request to the API
    response = client.post(
        "/generate-report", 
        json={
            "content": "We sang songs and learned about Noah's Ark",
            "image_paths": []
        }
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "notion_page_url" in data
    assert data["notion_page_url"] == "https://notion.so/new-page-id"
    assert len(data["report_content"]) == 2
    
    # Verify the mocks were called correctly
    mock_generate_report.assert_called_once()
    mock_create_page.assert_called_once()

@patch("main.gemini_client.generate_report", new_callable=AsyncMock)
def test_gemini_error_handling(mock_generate_report):
    """Test error handling when Gemini API fails."""
    # Mock the Gemini client to raise an exception
    mock_generate_report.side_effect = Exception("Gemini API error")
    
    # Send request to the API
    response = client.post(
        "/generate-report", 
        json={
            "content": "We sang songs and learned about Noah's Ark",
            "image_paths": []
        }
    )
    
    # Check response
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "Failed to generate report" in data["detail"]

@patch("main.os.remove")
@patch("main.save_upload_file", new_callable=AsyncMock)
@patch("main.notion_client.create_page", new_callable=AsyncMock)
@patch("main.gemini_client.generate_report", new_callable=AsyncMock)
def test_submit_form(mock_generate_report, mock_create_page, mock_save_upload, mock_os_remove):
    """Test the form submission endpoint."""
    # Mock the function responses
    mock_generate_report.return_value = "Today was a wonderful day in Sunday School!\n\nWe learned about important Bible stories."
    mock_create_page.return_value = ("https://notion.so/new-page-id", "new-page-id")
    mock_save_upload.return_value = "temp_image.jpg"
    
    # Create a mock file
    mock_file = MagicMock()
    mock_file.filename = "test.jpg"
    
    # Send request to the form endpoint
    response = client.post(
        "/submit-form",
        data={
            "content": "We sang songs and learned about Noah's Ark"
        },
        files={"images": ("test.jpg", b"test image content", "image/jpeg")}
    )
    
    # Check response
    assert response.status_code == 200
    assert "notion_page_url" in response.text
    assert "https://notion.so/new-page-id" in response.text
    
    # Verify the mocks were called correctly
    mock_generate_report.assert_called_once()
    mock_create_page.assert_called_once()
    mock_save_upload.assert_called_once()
    mock_os_remove.assert_called_once_with("temp_image.jpg")

if __name__ == "__main__":
    pytest.main(["-v", "test_app.py"])

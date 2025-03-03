import os
import re
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, validator
from dotenv import load_dotenv
from typing import Optional

from notion_client import NotionClient
from gemini_client import GeminiClient

# Load environment variables
load_dotenv()

app = FastAPI(title="Kindergarten Daily Report Generator")

# Initialize clients
notion_client = NotionClient(api_key=os.getenv("NOTION_API_KEY"))
gemini_client = GeminiClient(api_key=os.getenv("GEMINI_API_KEY"))

class NotionPageRequest(BaseModel):
    page_identifier: str
    
    @validator('page_identifier')
    def validate_page_identifier(cls, v):
        # Check if it's a URL or a page ID
        if v.startswith('http'):
            # Extract page ID from URL
            match = re.search(r'([a-f0-9]{32})', v)
            if not match:
                raise ValueError("Invalid Notion URL. Cannot extract page ID.")
            return match.group(1)
        elif re.match(r'^[a-f0-9]{32}$', v):
            # It's already a page ID
            return v
        else:
            raise ValueError("Invalid page identifier. Must be a Notion URL or a 32-character page ID.")

@app.get("/")
async def root():
    return {"message": "Kindergarten Daily Report Generator API"}

@app.post("/generate-report")
async def generate_report(request: NotionPageRequest):
    try:
        # 1. Extract content from the source Notion page
        page_content = notion_client.get_page_content(request.page_identifier)
        
        # 2. Generate daily report using Gemini API
        report_content = gemini_client.generate_report(page_content)
        
        # 3. Create a new Notion page with the report
        new_page_id = notion_client.create_report_page(report_content)
        
        # 4. Return the URL to the new page
        new_page_url = f"https://notion.so/{new_page_id.replace('-', '')}"
        
        return {
            "success": True,
            "report_url": new_page_url
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

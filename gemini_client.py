import google.generativeai as genai
from typing import Dict, List, Any

class GeminiClient:
    def __init__(self, api_key: str):
        """Initialize the Gemini client with the API key."""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def generate_report(self, page_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a kindergarten daily report using Gemini API based on the extracted Notion content.
        
        Args:
            page_content: Dictionary containing title, text content, and image URLs from the Notion page
            
        Returns:
            A dictionary containing the generated report title, content, and image URLs
        """
        # Extract content from the page_content
        title = page_content.get("title", "")
        text_content = page_content.get("text_content", [])
        image_urls = page_content.get("image_urls", [])
        
        # Combine all text content
        combined_text = "\n".join(text_content)
        
        # Create prompt for Gemini
        prompt = f"""
        You are a kindergarten teacher assistant. Your task is to generate a comprehensive daily report 
        for parents based on the following information from the classroom.
        
        Original Title: {title}
        
        Content from classroom notes:
        {combined_text}
        
        Number of photos taken: {len(image_urls)}
        
        Based on this information, please:
        1. Create a well-structured daily report with a title
        2. Organize activities in chronological order if possible
        3. Highlight key learning moments and achievements
        4. Use a warm, professional tone appropriate for parents
        5. Divide the report into clear sections (Morning Activities, Lunch, Afternoon Activities, etc.)
        6. Keep the original information but enhance it with educational context
        
        Format the response as a JSON-like structure with the following fields:
        - title: A descriptive title for the daily report
        - content: An array of paragraphs for the report
        """
        
        # Generate content with Gemini
        response = self.model.generate_content(prompt)
        
        # Process the response
        try:
            # Extract content from response
            response_text = response.text
            
            # Parse the response to extract title and content
            # This is a simplified parsing approach - in production, you might want to use a more robust method
            lines = response_text.strip().split('\n')
            
            # Extract title
            report_title = title
            for line in lines:
                if line.startswith('"title":') or line.startswith('- title:'):
                    report_title = line.split(':', 1)[1].strip().strip('"').strip(',')
                    break
            
            # Extract content
            report_content = []
            content_section = False
            for line in lines:
                if '"content":' in line or '- content:' in line:
                    content_section = True
                    continue
                
                if content_section and line.strip() and not line.strip().startswith('{') and not line.strip().startswith('}'):
                    # Clean up the line
                    cleaned_line = line.strip().strip('"').strip(',').strip('-').strip()
                    if cleaned_line:
                        report_content.append(cleaned_line)
            
            # If parsing fails, create a simple report
            if not report_content:
                report_title = title or "Kindergarten Daily Report"
                report_content = ["Today was a wonderful day at kindergarten!"]
                if combined_text:
                    report_content.append(combined_text)
        
        except Exception as e:
            # Fallback in case of parsing errors
            report_title = title or "Kindergarten Daily Report"
            report_content = [
                "Today was a wonderful day at kindergarten!",
                f"We had {len(image_urls)} exciting moments captured in photos."
            ]
            if combined_text:
                report_content.append(combined_text)
        
        # Return the generated report
        return {
            "title": report_title,
            "content": report_content,
            "image_urls": image_urls  # Reuse the original image URLs
        }

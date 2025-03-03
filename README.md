# Kindergarten Daily Report Generator

This project provides a simple API and web interface that allows users to generate kindergarten daily reports from a Notion page ID or link, publish them to Notion, and return a link to the new page.

## Features

- Web interface for easy report generation
- Accept Notion page ID or URL
- Extract text and photo URLs from Notion pages
- Generate daily reports using Gemini API
- Publish reports to new Notion pages
- Return links to the new pages

## Technical Architecture

- **Backend**: FastAPI (Python)
- **Frontend**: HTML/CSS with Jinja2 Templates
- **AI Generation**: Google Gemini API
- **Data Source/Target**: Notion API
- **Deployment**: Google Cloud Run

## Installation and Setup

### Prerequisites

- Python 3.9+
- Notion API key
- Gemini API key
- Notion database ID (for creating new pages)

### Local Development

1. Clone this project:

```bash
git clone <repository-url>
cd class-report
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables:

```bash
cp .env.example .env
```

Edit the `.env` file and fill in your API keys and database ID.

4. Run the application:

```bash
uvicorn main:app --reload
```

The application will run at `http://localhost:8000`.

## Usage

### Web Interface

1. Open your browser and navigate to `http://localhost:8000`
2. Enter your Notion page ID or URL in the form
3. Click "Generate Report"
4. You'll be redirected to a success page with a link to your new Notion report

### API Usage

If you prefer to use the API directly:

**Endpoint**: `POST /generate-report`

**Request Body**:

```json
{
  "page_identifier": "notion-page-ID-or-URL"
}
```

**Examples**:

```json
{
  "page_identifier": "https://www.notion.so/myworkspace/1234567890abcdef1234567890abcdef"
}
```

Or

```json
{
  "page_identifier": "1234567890abcdef1234567890abcdef"
}
```

**Response**:

```json
{
  "success": true,
  "report_url": "https://notion.so/new-page-ID"
}
```

## Deployment to Google Cloud Run

1. Ensure you have installed and configured the Google Cloud SDK.

2. Build and deploy to Cloud Run:

```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/class-report
gcloud run deploy class-report --image gcr.io/YOUR_PROJECT_ID/class-report --platform managed
```

3. Set environment variables:

In the Google Cloud Console, set the following environment variables for your Cloud Run service:
- `NOTION_API_KEY`
- `NOTION_DATABASE_ID`
- `GEMINI_API_KEY`

## Notion API Setup

1. Create a Notion integration: https://www.notion.so/my-integrations
2. Add the integration to your Notion workspace
3. Share the target database with your integration

## Important Notes

- Ensure your Notion API key has sufficient permissions to access the source page and target database
- Gemini API may incur costs; check Google AI Studio pricing
- This application only processes text and images, not other Notion block types

## License

[MIT License](LICENSE)

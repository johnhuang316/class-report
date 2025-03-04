# Kindergarten Daily Report Generator

This project provides a simple web interface that allows kindergarten teachers to generate daily reports by uploading photos and entering classroom notes. The system uses AI to generate a comprehensive report and publishes it to Notion, returning a link to the new page.

## Features

- Web interface for easy report generation
- Upload photos directly from your device
- Enter classroom notes and activities
- Generate AI-powered daily reports using Google Gemini
- Automatically publish reports to Notion
- Store images in Google Cloud Storage
- Return links to the new Notion pages

## Technical Architecture

- **Backend**: FastAPI (Python)
- **Frontend**: HTML/CSS/JavaScript with Jinja2 Templates
- **AI Generation**: Google Gemini API
- **Data Target**: Notion API
- **File Storage**: Google Cloud Storage (GCS)
- **Deployment**: Google Cloud Run

## Project Structure

```
class-report/
├── main.py                 # Main application file
├── requirements.txt        # Project dependencies
├── .env                    # Environment variables (not in repo)
├── .env.example            # Example environment variables
├── services/               # Service modules
│   ├── __init__.py         # Package initialization
│   ├── gemini_service.py   # Gemini AI integration
│   ├── notion_service.py   # Notion API integration
│   └── storage_service.py  # Google Cloud Storage integration
├── static/                 # Static files
│   ├── css/                # CSS stylesheets
│   │   └── styles.css      # Main stylesheet
│   ├── js/                 # JavaScript files
│   │   └── main.js         # Main JavaScript file
│   ├── img/                # Image assets
│   │   └── notion-logo.png # Notion logo
│   ├── uploads/            # Uploaded images (not in repo)
│   └── favicon.ico         # Favicon
└── templates/              # Jinja2 templates
    ├── index.html          # Home page template
    ├── success.html        # Success page template
    └── error.html          # Error page template
```

## Installation and Setup

### Prerequisites

- Python 3.9+
- Notion API key
- Gemini API key
- Notion database ID (for creating new pages)
- Google Cloud Storage bucket
- Google Cloud Service Account credentials

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

Edit the `.env` file and fill in your API keys, database ID, and Google Cloud Storage bucket name.

4. Run the application:

```bash
uvicorn main:app --reload
```

The application will run at `http://localhost:8000`.

## Usage

### Web Interface

1. Open your browser and navigate to `http://localhost:8000`
2. Upload photos from your device (multiple photos supported)
3. Enter classroom notes and activities in the text area
4. Click "Generate Report"
5. You'll be redirected to a success page with:
   - A link to your new Notion report
   - A preview of the generated report content
   - The uploaded images

### API Usage

If you prefer to use the API directly:

**Endpoint**: `POST /generate-report`

**Request Body**:

```json
{
  "content": ["Classroom notes and activities"],
  "image_paths": ["/path/to/image1.jpg", "/path/to/image2.jpg"]
}
```

**Response**:

```json
{
  "success": true,
  "report_id": "unique-report-id",
  "notion_page_id": "notion-page-id",
  "notion_page_url": "https://notion.so/page-id"
}
```

## Deployment to Google Cloud Run

### Important Security Note

For security reasons, all sensitive information (API keys, credentials, etc.) should be stored in environment variables using a `.env` file. Never commit sensitive information directly to the repository.

1. Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

2. Update the `.env` file with your actual credentials:
```
NOTION_API_KEY=your_notion_api_key
NOTION_DATABASE_ID=your_database_id
GEMINI_API_KEY=your_gemini_api_key
GCS_BUCKET_NAME=your_bucket_name
```

3. Ensure `.env` is listed in your `.gitignore` file to prevent accidental commits.

### Using Deployment Scripts

This project includes deployment scripts for both Linux/Mac (bash) and Windows (PowerShell) environments.

#### For Linux/Mac Users:

1. Ensure you have installed and configured the Google Cloud SDK.
2. Make sure your `.env` file is properly configured.
3. Make the script executable and run it:

```bash
chmod +x deploy.sh
./deploy.sh
```

#### For Windows Users:

1. Ensure you have installed and configured the Google Cloud SDK.
2. Make sure your `.env` file is properly configured.
3. Run the PowerShell script:

```powershell
.\deploy.ps1
```

### Manual Deployment

If you prefer to deploy manually:

1. Build the Docker image:

```bash
docker build -t gcr.io/YOUR_PROJECT_ID/class-report .
```

2. Push the image to Google Container Registry:

```bash
docker push gcr.io/YOUR_PROJECT_ID/class-report
```

3. Deploy to Cloud Run:

```bash
gcloud run deploy class-report \
  --image gcr.io/YOUR_PROJECT_ID/class-report \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="NOTION_API_KEY=,NOTION_DATABASE_ID=,GEMINI_API_KEY=,GCS_BUCKET_NAME="
```

### Environment Variables

In the Google Cloud Console, set the following environment variables for your Cloud Run service:
- `NOTION_API_KEY`: Your Notion integration API key
- `NOTION_DATABASE_ID`: ID of the Notion database where reports will be created
- `GEMINI_API_KEY`: Your Google Gemini API key
- `GCS_BUCKET_NAME`: Name of your Google Cloud Storage bucket
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to your service account JSON file (or use mounted secrets in Cloud Run)

## Storage Service

The application uses Google Cloud Storage (GCS) to store uploaded images. The `storage_service.py` module handles image uploads and storage.

### Environment Variables

To use the Storage Service, you need to set the following environment variables:

- `GCS_BUCKET_NAME`: Name of your Google Cloud Storage bucket
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to your service account JSON file

### Optional Feature

The Storage Service is optional. If you don't set the GCS environment variables, the application will still work, but images will only be available locally and won't be uploaded to cloud storage.

### Image Upload

When you upload an image, the application will:
1. Save the image temporarily to the local filesystem in the `temp` directory
2. Upload the image to the GCS bucket and get a public URL
3. Use the image URL in the Notion page
4. Delete the temporary local file after it's been uploaded to GCS

This ensures that images are stored in Google Cloud Storage and not on the local system, which is more suitable for production environments and provides better durability and availability.

## Monitoring and Troubleshooting

### Logs

The application includes comprehensive logging to help diagnose issues:

- **Application Logs**: Available in Cloud Run console under the "Logs" tab
- **Local Logs**: When running locally, logs are output to the console

### Common Issues

1. **API Key Issues**: Ensure your API keys are correctly set in environment variables
2. **Notion Permission Issues**: Verify your integration has access to both source pages and target database
3. **Gemini API Errors**: Check quota limits and API key validity

## Performance Optimization

The application is configured with the following Cloud Run settings:

- Memory: 512Mi
- CPU: 1
- Concurrency: 80 (maximum concurrent requests per instance)
- Max instances: 10 (to control costs)
- Min instances: 0 (scales to zero when not in use)

Adjust these settings in the deployment scripts or Cloud Run console based on your usage patterns.

## Security Considerations

- API keys are stored as environment variables and never exposed in logs
- The application runs as a non-root user in the container
- HTTPS is enforced by Cloud Run
- Input validation is implemented for all user inputs

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

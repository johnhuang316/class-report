# PowerShell Deployment script for Google Cloud Run

# Load environment variables from .env file
function Load-EnvFile {
    if (Test-Path .env) {
        Get-Content .env | ForEach-Object {
            if ($_ -match '^([^=]+)=(.*)$') {
                $key = $matches[1]
                $value = $matches[2]
                Set-Item "env:$key" $value
            }
        }
        Write-Host "Environment variables loaded from .env file"
    } else {
        Write-Host "Warning: .env file not found. Please create one based on .env.example"
        exit 1
    }
}

# Load environment variables
Load-EnvFile

# Configuration - load from environment variables with fallbacks
$PROJECT_ID = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "jumido" }
$SERVICE_NAME = if ($env:SERVICE_NAME) { $env:SERVICE_NAME } else { "class-report" }
$REGION = if ($env:GCP_REGION) { $env:GCP_REGION } else { "us-central1" }
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Verify required environment variables
$requiredEnvVars = @(
    "NOTION_API_KEY",
    "NOTION_DATABASE_ID",
    "GEMINI_API_KEY",
    "GCS_BUCKET_NAME"
)

# Verify optional environment variables with defaults
$optionalEnvVars = @(
    @{Name = "GCP_PROJECT_ID"; Default = "jumido"; Description = "Google Cloud Project ID"},
    @{Name = "SERVICE_NAME"; Default = "class-report"; Description = "Cloud Run service name"},
    @{Name = "GCP_REGION"; Default = "us-central1"; Description = "Google Cloud region"}
)

# Log environment configuration
Write-Host "Deployment Configuration:"
Write-Host "  Project ID: $PROJECT_ID"
Write-Host "  Service Name: $SERVICE_NAME"
Write-Host "  Region: $REGION"
Write-Host "  Image: $IMAGE_NAME"

foreach ($var in $requiredEnvVars) {
    if (-not (Get-Item "env:$var" -ErrorAction SilentlyContinue)) {
        Write-Host "Error: Missing required environment variable: $var"
        exit 1
    }
}

# Build the container image
Write-Host "Building container image: $IMAGE_NAME"
gcloud builds submit --tag $IMAGE_NAME

# Deploy to Cloud Run
Write-Host "Deploying to Cloud Run in $REGION"
gcloud run deploy $SERVICE_NAME `
    --image $IMAGE_NAME `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --set-env-vars="NOTION_API_KEY=$env:NOTION_API_KEY,NOTION_DATABASE_ID=$env:NOTION_DATABASE_ID,GEMINI_API_KEY=$env:GEMINI_API_KEY,GCS_BUCKET_NAME=$env:GCS_BUCKET_NAME" `
    --memory 256Mi `
    --cpu 1 `
    --concurrency 80 `
    --max-instances 3 `
    --min-instances 0

Write-Host "Deployment complete! Your service will be available at the URL shown above."

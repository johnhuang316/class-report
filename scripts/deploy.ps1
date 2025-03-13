# PowerShell Deployment script for Google Cloud Run

# Get script directory and project root
$scriptPath = $PSScriptRoot
$projectRoot = Split-Path -Parent $scriptPath

# Load environment variables from .env file
function Import-EnvFile {
    $envPath = Join-Path $projectRoot ".env"
    if (Test-Path $envPath) {
        Get-Content $envPath | ForEach-Object {
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
Import-EnvFile

# Configuration - load from environment variables without defaults
$PROJECT_ID = $env:GCP_PROJECT_ID
$SERVICE_NAME = $env:SERVICE_NAME
$REGION = $env:GCP_REGION
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Verify required environment variables
$requiredEnvVars = @(
    "NOTION_API_KEY",
    "NOTION_DATABASE_ID",
    "GEMINI_API_KEY",
    "GCS_BUCKET_NAME",
    "OUTPUT_PLATFORM"
)

# Verify environment variables that were previously optional
$additionalEnvVars = @(
    @{Name = "GCP_PROJECT_ID"; Description = "Google Cloud Project ID"},
    @{Name = "SERVICE_NAME"; Description = "Cloud Run service name"},
    @{Name = "GCP_REGION"; Description = "Google Cloud region"}
)

# Log environment configuration
Write-Host "Deployment Configuration:"
Write-Host "  Project ID: $PROJECT_ID"
Write-Host "  Service Name: $SERVICE_NAME"
Write-Host "  Region: $REGION"
Write-Host "  Image: $IMAGE_NAME"

# Check all required environment variables
foreach ($var in $requiredEnvVars) {
    if (-not (Get-Item "env:$var" -ErrorAction SilentlyContinue)) {
        Write-Host "Error: Missing required environment variable: $var"
        exit 1
    }
}

# Check previously optional environment variables that are now required
foreach ($var in $additionalEnvVars) {
    if (-not (Get-Item "env:$($var.Name)" -ErrorAction SilentlyContinue)) {
        Write-Host "Error: Missing required environment variable: $($var.Name) - $($var.Description)"
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
    --set-env-vars="NOTION_API_KEY=$env:NOTION_API_KEY,NOTION_DATABASE_ID=$env:NOTION_DATABASE_ID,GEMINI_API_KEY=$env:GEMINI_API_KEY,GCS_BUCKET_NAME=$env:GCS_BUCKET_NAME,OUTPUT_PLATFORM=$env:OUTPUT_PLATFORM" `
    --memory 256Mi `
    --cpu 1 `
    --concurrency 80 `
    --max-instances 3 `
    --min-instances 0

Write-Host "Deployment complete! Your service will be available at the URL shown above."

# Upload website files to GCS bucket root
Write-Host "Uploading website files to GCS bucket root..."
& "$PSScriptRoot\upload_website.ps1"

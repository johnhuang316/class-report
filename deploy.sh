#!/bin/bash
# Deployment script for Google Cloud Run

# Load environment variables from .env file
if [ -f .env ]; then
    echo "Loading environment variables from .env file"
    set -a
    source .env
    set +a
else
    echo "Error: .env file not found. Please create one based on .env.example"
    exit 1
fi

# Configuration - load from environment variables without defaults
PROJECT_ID="${GCP_PROJECT_ID}"
SERVICE_NAME="${SERVICE_NAME}"
REGION="${GCP_REGION}"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Check required environment variables
required_vars=(
    "NOTION_API_KEY"
    "NOTION_DATABASE_ID"
    "GEMINI_API_KEY"
    "GCS_BUCKET_NAME"
    "OUTPUT_PLATFORM"
)

# Previously hardcoded variables that are now required
additional_vars=(
    "GCP_PROJECT_ID:Google Cloud Project ID"
    "SERVICE_NAME:Cloud Run service name"
    "GCP_REGION:Google Cloud region"
)

# Check all required environment variables
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: Required environment variable $var is not set"
        exit 1
    fi
done

# Check previously hardcoded variables that are now required
for var_info in "${additional_vars[@]}"; do
    var_name="${var_info%%:*}"
    var_desc="${var_info#*:}"
    if [ -z "${!var_name}" ]; then
        echo "Error: Missing required environment variable: $var_name - $var_desc"
        exit 1
    fi
done

# Build the container image
echo "Building container image: ${IMAGE_NAME}"
gcloud builds submit --tag ${IMAGE_NAME}

# Deploy to Cloud Run
echo "Deploying to Cloud Run in ${REGION}"
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --set-env-vars="NOTION_API_KEY=${NOTION_API_KEY},NOTION_DATABASE_ID=${NOTION_DATABASE_ID},GEMINI_API_KEY=${GEMINI_API_KEY},GCS_BUCKET_NAME=${GCS_BUCKET_NAME},OUTPUT_PLATFORM=${OUTPUT_PLATFORM}" \
    --memory 256Mi \
    --cpu 1 \
    --concurrency 80 \
    --max-instances 3 \
    --min-instances 0

echo "Deployment complete! Your service will be available at the URL shown above."

# Upload website files to GCS bucket root
echo "Uploading website files to GCS bucket root..."
"$SCRIPT_DIR/scripts/upload_website.sh"

echo "Website files uploaded successfully to GCS bucket root"

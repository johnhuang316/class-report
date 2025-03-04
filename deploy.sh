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

# Configuration - change these values as needed
PROJECT_ID="jumido"
SERVICE_NAME="class-report"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Check required environment variables
required_vars=(
    "NOTION_API_KEY"
    "NOTION_DATABASE_ID"
    "GEMINI_API_KEY"
    "GCS_BUCKET_NAME"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: Required environment variable $var is not set"
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
    --set-env-vars="NOTION_API_KEY=${NOTION_API_KEY},NOTION_DATABASE_ID=${NOTION_DATABASE_ID},GEMINI_API_KEY=${GEMINI_API_KEY},GCS_BUCKET_NAME=${GCS_BUCKET_NAME}" \
    --memory 256Mi \
    --cpu 1 \
    --concurrency 80 \
    --max-instances 3 \
    --min-instances 0

echo "Deployment complete! Your service will be available at the URL shown above."

#!/bin/bash
set -e  # Exit on error

# Upload website files to GCS bucket root
echo "Uploading website files to GCS bucket root..."

# Get script directory and construct website folder path
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
WEBSITE_FOLDER="$PROJECT_ROOT/website"

echo "Looking for website folder at: $WEBSITE_FOLDER"

# Check if website folder exists
if [ -d "$WEBSITE_FOLDER" ]; then
    # Get all files in the website folder
    find "$WEBSITE_FOLDER" -type f | while read -r file; do
        # Calculate relative path
        relative_path="${file#$WEBSITE_FOLDER/}"
        echo "Uploading $(basename "$file") to gs://$GCS_BUCKET_NAME/$relative_path"
        
        # Upload file to GCS bucket root
        gsutil cp "$file" "gs://$GCS_BUCKET_NAME/$relative_path"
    done
    
    echo "Website files uploaded successfully to GCS bucket root"
else
    echo "Warning: Website folder not found at $WEBSITE_FOLDER"
    exit 1
fi

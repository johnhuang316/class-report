#!/bin/bash
set -e  # Exit on error

# Upload website files to GCS bucket root
echo "Uploading website files to GCS bucket root..."
BUCKET_NAME="$GCS_BUCKET_NAME"

# Get script directory and construct website folder path
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
WEBSITE_FOLDER="$PROJECT_ROOT/website"

echo "Looking for website folder at: $WEBSITE_FOLDER"

# Check if website folder exists
if [ -d "$WEBSITE_FOLDER" ]; then
    # Get absolute path of website folder
    WEBSITE_FOLDER_ABSOLUTE="$(cd "$WEBSITE_FOLDER" && pwd)"
    echo "Website folder absolute path: $WEBSITE_FOLDER_ABSOLUTE"
    
    # Get all files in the website folder
    FILES=$(find "$WEBSITE_FOLDER" -type f)
    
    # List all files to be uploaded
    echo "Will upload the following files:"
    FILES_TO_UPLOAD=()
    for file in $FILES; do
        relative_path="${file#$WEBSITE_FOLDER_ABSOLUTE/}"
        FILES_TO_UPLOAD+=("$relative_path")
        echo "- $relative_path"
    done
    
    # Check and delete existing files with the same name
    echo "Checking for existing files in GCS bucket..."
    for relative_path in "${FILES_TO_UPLOAD[@]}"; do
        # Check if file exists
        if gsutil -q stat "gs://$BUCKET_NAME/$relative_path" 2>/dev/null; then
            echo "Removing existing file: gs://$BUCKET_NAME/$relative_path"
            gsutil rm -f "gs://$BUCKET_NAME/$relative_path" 2>/dev/null
        fi
    done
    
    # Upload all files
    for file in $FILES; do
        # Get the correct relative path
        relative_path="${file#$WEBSITE_FOLDER_ABSOLUTE/}"
        echo "Uploading $(basename "$file") to gs://$BUCKET_NAME/$relative_path"
        
        # Set Cache-Control based on file type
        extension="${file##*.}"
        case "$extension" in
            html)
                content_type="text/html"
                ;;
            css)
                content_type="text/css"
                ;;
            js)
                content_type="application/javascript"
                ;;
            png)
                content_type="image/png"
                ;;
            jpg|jpeg)
                content_type="image/jpeg"
                ;;
            ico)
                content_type="image/x-icon"
                ;;
            *)
                content_type="application/octet-stream"
                ;;
        esac
        
        # Upload file and set metadata
        gsutil -h "Cache-Control:no-cache,max-age=0" -h "Content-Type:$content_type" cp "$file" "gs://$BUCKET_NAME/$relative_path"
    done
    
    echo "Website files uploaded successfully to GCS bucket root"
else
    echo "Warning: Website folder not found at $WEBSITE_FOLDER"
    exit 1
fi

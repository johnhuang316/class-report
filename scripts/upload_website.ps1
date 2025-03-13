# Upload website files to GCS bucket root
Write-Host "Uploading website files to GCS bucket root..."
$bucketName = $env:GCS_BUCKET_NAME

# Get script directory and construct website folder path
$scriptPath = $PSScriptRoot
$projectRoot = Split-Path -Parent $scriptPath
$websiteFolder = Join-Path $projectRoot "website"

Write-Host "Looking for website folder at: $websiteFolder"

# Check if website folder exists
if (Test-Path $websiteFolder) {
    # Get absolute path of website folder
    $websiteFolderAbsolute = (Get-Item $websiteFolder).FullName
    Write-Host "Website folder absolute path: $websiteFolderAbsolute"
    
    # Get all files in the website folder
    $files = Get-ChildItem -Path $websiteFolder -File -Recurse
    
    # List all files to be uploaded
    Write-Host "Will upload the following files:"
    $filesToUpload = @()
    foreach ($file in $files) {
        $relativePath = $file.FullName.Replace($websiteFolderAbsolute, "").TrimStart("\")
        $filesToUpload += $relativePath
        Write-Host "- $relativePath"
    }
    
    # Check and delete existing files with the same name
    Write-Host "Checking for existing files in GCS bucket..."
    foreach ($relativePath in $filesToUpload) {
        # Check if file exists
        $fileExists = gsutil -q stat "gs://$bucketName/$relativePath" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Removing existing file: gs://$bucketName/$relativePath"
            gsutil rm -f "gs://$bucketName/$relativePath" 2>$null
        }
    }
    
    # Upload all files
    foreach ($file in $files) {
        # Use Replace to get the correct relative path
        $relativePath = $file.FullName.Replace($websiteFolderAbsolute, "").TrimStart("\")
        Write-Host "Uploading $($file.Name) to gs://$bucketName/$relativePath"
        
        # Set Cache-Control based on file type
        $contentType = switch ($file.Extension) {
            ".html" { "text/html" }
            ".css"  { "text/css" }
            ".js"   { "application/javascript" }
            ".png"  { "image/png" }
            ".jpg"  { "image/jpeg" }
            ".ico"  { "image/x-icon" }
            default { "application/octet-stream" }
        }
        
        # Upload file and set metadata
        gsutil -h "Cache-Control:no-cache,max-age=0" -h "Content-Type:$contentType" cp $file.FullName "gs://$bucketName/$relativePath"
    }
    
    Write-Host "Website files uploaded successfully to GCS bucket root"
} else {
    Write-Host "Warning: Website folder not found at $websiteFolder"
}
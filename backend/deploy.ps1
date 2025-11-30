# Deploy backend to Azure App Service with all configuration

Write-Host "=== Deploying Asia's Panel Backend to Azure ===" -ForegroundColor Cyan

# Check if we're in the backend directory
if (!(Test-Path "app.py")) {
    Write-Host "Error: Please run this script from the backend directory" -ForegroundColor Red
    exit 1
}

# Auto-load .env.production if it exists and variables not already set
if ((Test-Path ".env.production") -and (!$env:OPENAI_API_KEY -or !$env:AZURE_STORAGE_CONNECTION_STRING -or !$env:ELEVENLABS_API_KEY)) {
    Write-Host "Loading environment variables from .env.production..." -ForegroundColor Yellow
    Get-Content .env.production | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            if ($key -and !$key.StartsWith('#')) {
                Set-Item -Path "env:$key" -Value $value
                Write-Host "  Loaded: $key" -ForegroundColor Gray
            }
        }
    }
}

# Check environment variables
if (!$env:OPENAI_API_KEY) {
    Write-Host "Warning: OPENAI_API_KEY not set in environment" -ForegroundColor Yellow
    Write-Host "  Set manually: `$env:OPENAI_API_KEY='your-key'" -ForegroundColor Gray
    Write-Host "  Or create .env.production file" -ForegroundColor Gray
}
if (!$env:AZURE_STORAGE_CONNECTION_STRING) {
    Write-Host "Warning: AZURE_STORAGE_CONNECTION_STRING not set in environment" -ForegroundColor Yellow
    Write-Host "  Set manually: `$env:AZURE_STORAGE_CONNECTION_STRING='your-connection-string'" -ForegroundColor Gray
    Write-Host "  Or create .env.production file" -ForegroundColor Gray
}
if (!$env:ELEVENLABS_API_KEY) {
    Write-Host "Warning: ELEVENLABS_API_KEY not set in environment" -ForegroundColor Yellow
    Write-Host "  Set manually: `$env:ELEVENLABS_API_KEY='your-key'" -ForegroundColor Gray
    Write-Host "  Or create .env.production file" -ForegroundColor Gray
}

# Deploy app
Write-Host "`nDeploying app..." -ForegroundColor Green
az webapp up --name asiaspanel-backend --runtime PYTHON:3.11 --sku B1 --location westeurope --resource-group asiaspanel-web2

if ($LASTEXITCODE -ne 0) {
    Write-Host "Deployment failed!" -ForegroundColor Red
    exit 1
}

# Set environment variables
Write-Host "`nConfiguring environment variables..." -ForegroundColor Green
az webapp config appsettings set --name asiaspanel-backend --resource-group asiaspanel-web2 --settings `
    OPENAI_API_KEY="$env:OPENAI_API_KEY" `
    AZURE_STORAGE_CONNECTION_STRING="$env:AZURE_STORAGE_CONNECTION_STRING" `
    ELEVENLABS_API_KEY="$env:ELEVENLABS_API_KEY" `
    AZURE_TTS_CONTAINER="tts-audio" `
    BACKEND_URL="https://asiaspanel-backend.azurewebsites.net"

# Set startup command
Write-Host "`nConfiguring startup command..." -ForegroundColor Green
az webapp config set --name asiaspanel-backend --resource-group asiaspanel-web2 --startup-file "python -m uvicorn app:app --host 0.0.0.0 --port 8000"

# Enable CORS
Write-Host "`nEnabling CORS..." -ForegroundColor Green
az webapp cors add --name asiaspanel-backend --resource-group asiaspanel-web2 --allowed-origins "https://proud-mud-09bc94003.3.azurestaticapps.net"

# Restart app
Write-Host "`nRestarting app..." -ForegroundColor Green
az webapp restart --name asiaspanel-backend --resource-group asiaspanel-web2

Write-Host "`n=== Deployment Complete ===" -ForegroundColor Cyan
Write-Host "Backend URL: https://asiaspanel-backend.azurewebsites.net" -ForegroundColor Green
# Write-Host "`nTesting health endpoint..." -ForegroundColor Yellow
# Start-Sleep -Seconds 10
# curl https://asiaspanel-backend.azurewebsites.net/health

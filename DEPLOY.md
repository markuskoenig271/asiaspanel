# Backend Deployment Guide

## Quick Deploy (Existing App)

```powershell
cd backend
.\deploy.ps1
```

## Delete and Redeploy from Scratch

### Step 1: Delete Existing Backend

```powershell
# Delete the backend App Service
az webapp delete --name asiaspanel-backend --resource-group asiaspanel-web2

# Delete the App Service Plan (optional - saves cost)
az appservice plan delete --name markus_koenig73_asp_2017 --resource-group asiaspanel-web2
```

### Step 2: Set Environment Variables

**Option A: Create `.env.production` file (Recommended)**
```powershell
# Copy example and edit with your actual keys
copy .env.production.example .env.production
notepad .env.production

# The deploy.ps1 script will automatically load this file!
```

**Note**: The `deploy.ps1` script automatically loads `.env.production` if it exists, so you don't need to manually load it!

### Step 3: Deploy Fresh

```powershell
cd backend
powershell -ExecutionPolicy Bypass -File .\deploy.ps1
```

The script will automatically:
- Deploy the app with Python 3.11
- Configure environment variables from `.env.production` or current session
- Set the Uvicorn startup command
- Enable CORS for your frontend
- Restart the app
- Test the health endpoint

### Step 4: Verify

```powershell
curl https://asiaspanel-backend.azurewebsites.net/health
```

## Files

- `.azure/config` - Azure CLI defaults (resource group, location)
- `startup.txt` - Uvicorn startup command
- `deploy.ps1` - Automated deployment script
- `.env.production.example` - Example environment variables
- `DEPLOY.md` - This file

## Troubleshooting

### Build Logs
```powershell
az webapp log tail --name asiaspanel-backend --resource-group asiaspanel-web2
```

### Deployment History
```powershell
az webapp log deployment show --name asiaspanel-backend --resource-group asiaspanel-web2
```

### Download Full Logs
```powershell
az webapp log download --name asiaspanel-backend --resource-group asiaspanel-web2 --log-file logs.zip
```

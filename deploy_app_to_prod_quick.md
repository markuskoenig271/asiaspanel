# Deploy App to Production - Quick Guide

## Prerequisites

```powershell
# Install Azure CLI (if not installed)
winget install Microsoft.AzureCLI

# Login to Azure
az login
```

---

## Part 1: Deploy Frontend

```bash
# 1. Commit all changes
git add .
git commit -m "Add voice recording and file logging features"

# 2. Push to master (triggers automatic deployment)
git push origin master
```

**Monitor deployment**: https://github.com/markuskoenig271/asiaspanel/actions

**Get URL**:
```powershell
az staticwebapp show --name asiaspanel --resource-group <RESOURCE_GROUP> --query defaultHostname -o tsv
```

**Result**: `https://proud-mud-09bc94003.azurestaticapps.net` (or your actual URL)

---

## Part 2: Deploy Backend (Azure App Service)

```powershell
# 1. Deploy backend (one command from backend folder)
cd C:\Users\marku\Documents\2025\93_Project_AI\repos\asiaspanel\backend
az webapp up --name asiaspanel-backend --runtime PYTHON:3.11 --sku B1 --location eastus
```

**Note**: If name taken, try `asiaspanel-backend-yourname`

```powershell
# 2. Configure environment variables
az webapp config appsettings set --name asiaspanel-backend --settings OPENAI_API_KEY="your-openai-key-here"

az webapp config appsettings set --name asiaspanel-backend --settings AZURE_STORAGE_CONNECTION_STRING="your-connection-string"

az webapp config appsettings set --name asiaspanel-backend --settings AZURE_TTS_CONTAINER="tts-audio"

# 3. Get backend URL
az webapp show --name asiaspanel-backend --query defaultHostName -o tsv

# 4. Test backend
curl https://asiaspanel-backend.azurewebsites.net/health

# 5. Enable CORS
az webapp cors add --name asiaspanel-backend --allowed-origins "https://proud-mud-09bc94003.azurestaticapps.net"
```

**Replace with your actual Static Web App URL**

---

## Part 3: Connect Frontend to Backend

Edit `asiaspanel-web2/index.html`:

**Find**:
```javascript
const API_BASE = '';
```

**Replace with**:
```javascript
const API_BASE = window.location.hostname.includes('azurestaticapps.net') 
  ? 'https://asiaspanel-backend.azurewebsites.net' 
  : '';
```

**Deploy updated frontend**:
```bash
git add asiaspanel-web2/index.html
git commit -m "Connect frontend to production backend"
git push origin master
```

---

## Verify Deployment

Open production URL and test:
- ✅ Page loads
- ✅ TTS works
- ✅ Voice recording works
- ✅ Replay button works
- ✅ Translate works

---

## URLs

- **Frontend**: `https://proud-mud-09bc94003.azurestaticapps.net`
- **Backend**: `https://asiaspanel-backend.azurewebsites.net`
- **Cost**: ~$13/month (B1 tier) or Free (F1 tier)

---

## Update/Redeploy

```bash
# Make changes, then:
git add .
git commit -m "Your update"
git push origin master
```

Frontend redeploys automatically. Backend redeploy:
```powershell
cd backend
az webapp up --name asiaspanel-backend
```

---

**Deployment time**: ~5-10 minutes total

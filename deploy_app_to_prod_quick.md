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
az staticwebapp show --name asiaspanel-web2 --resource-group asiaspanel-web2 --query defaultHostname -o tsv
```

**Result**: `https://proud-mud-09bc94003.3.azurestaticapps.net` (or your actual URL)


---

## Part 2: Deploy Backend (Azure App Service)

```powershell
# 1. Deploy backend (one command from backend folder)
cd C:\Users\marku\Documents\2025\93_Project_AI\repos\asiaspanel\backend
az webapp up --name asiaspanel-backend --runtime PYTHON:3.11 --sku B1 --location westeurope --resource-group asiaspanel-web2

```

**Note**: If name taken, try `asiaspanel-backend-yourname`. The `--resource-group` flag ensures it's created in the same resource group as your frontend.

```powershell
# 2. Configure environment variables
az webapp config appsettings set --name asiaspanel-backend --settings OPENAI_API_KEY="your-openai-key-here"

az webapp config appsettings set --name asiaspanel-backend --settings AZURE_STORAGE_CONNECTION_STRING="your-connection-string"

az webapp config appsettings set --name asiaspanel-backend --settings AZURE_TTS_CONTAINER="tts-audio"

# 2b. Set startup command (REQUIRED - tells Azure to use Uvicorn for FastAPI)
az webapp config set --name asiaspanel-backend --resource-group asiaspanel-web2 --startup-file "python -m uvicorn app:app --host 0.0.0.0 --port 8000"

# 2b1. Enable CORS
az webapp cors add --name asiaspanel-backend --resource-group asiaspanel-web2 --allowed-origins "https://proud-mud-09bc94003.3.azurestaticapps.net"

# 2c. Restart app to apply changes
az webapp restart --name asiaspanel-backend --resource-group asiaspanel-web2

# check if running
az webapp log tail --name asiaspanel-backend --resource-group asiaspanel-web2

# 3. Get backend URL
az webapp show --name asiaspanel-backend --query defaultHostName -o tsv

# 4. Test backend
curl https://asiaspanel-backend.azurewebsites.net/health


                                                               
```

**Replace with your actual Static Web App URL**

---

## Part 3: Connect Frontend to Backend (One-Time Setup)

Edit `asiaspanel-web2/index.html` **once** to auto-detect the environment:

**Find**:
```javascript
const API_BASE = '';
```

**Replace with** (auto-detects local vs production):
```javascript
// Auto-detect: production uses Azure backend, local uses localhost
const API_BASE = window.location.hostname.includes('azurestaticapps.net') 
  ? 'https://asiaspanel-backend.azurewebsites.net' 
  : '';
```

**Deploy this change once**:
```bash
git add asiaspanel-web2/index.html
git commit -m "Add auto-detect for production backend"
git push origin master
```

**How it works:**
- 🏠 **Local** (`http://localhost:8001`): `API_BASE = ''` → calls same origin
- ☁️ **Production** (`https://*.azurestaticapps.net`): `API_BASE = 'https://asiaspanel-backend.azurewebsites.net'` → calls Azure backend
- ✅ **No more manual changes needed** - works everywhere automatically!

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
- **Frontend**: `https://proud-mud-09bc94003.3.azurestaticapps.net`
- **Backend**: `https://asiaspanel-backend.azurewebsites.net`
- **Cost**: ~$13/month (B1 tier) or Free (F1 tier)

---

## Update/Redeploy

### Frontend

```bash
# Make changes, then:
git add .
git commit -m "Your update"
git push origin master
```

Frontend redeploys automatically.

### Backend redeploy:

try shortest change if only code change

```powershell

az webapp up --name asiaspanel-backend


az webapp config set --name asiaspanel-backend --resource-group asiaspanel-web2 --linux-fx-version "PYTHON|3.11"

cd C:\Users\marku\Documents\2025\93_Project_AI\repos\asiaspanel\backend
az webapp up --name asiaspanel-backend --runtime PYTHON:3.11
```

**Note**: `az webapp up` detects it's an update and only uploads changed files (much faster than initial deployment).

---

**Deployment time**: ~5-10 minutes total

# Deploy App to Production

This runbook explains how to deploy the asiaspanel application to production using GitHub Actions and Azure Static Web Apps.

## Overview

The application consists of two parts:
- **Frontend**: Static HTML/JS app (`asiaspanel-web2/` folder) → deploys to Azure Static Web Apps
- **Backend**: FastAPI Python app (`backend/app.py`) → requires separate deployment (see Backend Deployment section)

The GitHub Actions workflow automatically deploys the frontend when you push to the `master` branch.

---

## Prerequisites

1. **GitHub repository** with code pushed to remote
2. **Azure Static Web App** created and linked to your GitHub repo
3. **GitHub Actions workflow** file already exists at:
   `.github/workflows/azure-static-web-apps-proud-mud-09bc94003.yml`
4. **Azure credentials** configured as GitHub secrets:
   - `AZURE_STATIC_WEB_APPS_API_TOKEN_PROUD_MUD_09BC94003`

---

## Frontend Deployment (Automatic)

### Step 1: Commit Your Changes

Make sure all changes are committed locally:

```bash
# Check status
git status

# Add all changes
git add .

# Commit with descriptive message
git commit -m "Add voice recording feature and file logging"
```

### Step 2: Push to Master Branch

```bash
# Push to remote master branch
git push origin master
```

### Step 3: Monitor GitHub Actions

1. Go to your GitHub repository: `https://github.com/markuskoenig271/asiaspanel`
2. Click the **Actions** tab
3. You'll see the workflow run "Azure Static Web Apps CI/CD"
4. Click on the running job to see real-time logs
5. Wait for the job to complete (typically 1-3 minutes)

### Step 4: Get Your Production URL

**Option A - From GitHub Actions:**
- Check the Actions job summary/logs for the deployed URL

**Option B - Azure CLI:**
```powershell
az staticwebapp show --name asiaspanel --resource-group <RESOURCE_GROUP> --query defaultHostname -o tsv
```

**Option C - Azure Portal:**
1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Static Web Apps**
3. Select your app (asiaspanel)
4. Copy the URL from the **Overview** page

Your production URL will be similar to:
```
https://proud-mud-09bc94003.azurestaticapps.net
```

### Step 5: Verify Deployment

Open the production URL in your browser and verify:
- ✅ Page loads correctly
- ✅ Voice selector dropdown works
- ✅ Translate feature works (if backend is deployed)
- ✅ TTS feature works (if backend is deployed)
- ✅ Voice recording UI appears
- ✅ Replay button appears

---

## Making Updates and Redeploying

To deploy updates, simply repeat the process:

```bash
# Make your code changes
# ...

# Commit and push
git add .
git commit -m "Update feature X"
git push origin master
```

GitHub Actions will automatically redeploy within minutes.

---

## Backend Deployment

⚠️ **Important**: The current setup **only deploys the frontend**. The backend API (`backend/app.py`) is not deployed automatically.

### Current Limitation

The workflow configuration has:
```yaml
app_location: "asiaspanel-web2"  # Frontend only
api_location: ""                  # No backend deployment
```

### Backend Deployment Options - Comparison

#### Option 2: Azure App Service (⭐ RECOMMENDED)

**What it is**: Platform-as-a-Service (PaaS) - you give Azure your Python code, they handle everything

**Pros:**
- ✅ Simplest deployment (one command)
- ✅ Cheapest option (~$13/month for B1 tier, or Free F1 tier)
- ✅ No code changes needed - deploy FastAPI as-is
- ✅ Built-in HTTPS with automatic SSL certificates
- ✅ Easy environment variable configuration
- ✅ You manage: Just your code
- ✅ Azure manages: OS, Python runtime, scaling, load balancing

**Cons:**
- ❌ Always running (no scale-to-zero)
- ❌ Less flexible than containers

**Best for**: Simple web apps like yours - fastest to deploy, most cost-effective

**Cost**: 
- **F1 Free tier**: $0/month (limited, good for testing)
- **B1 tier**: ~$13/month (1 core, 1.75GB RAM - plenty for this app)

---

#### Option 3: Azure Functions (Serverless)

**What it is**: Serverless compute - pay only when code runs

**Pros:**
- ✅ Scales to zero (very cheap for low-traffic apps)
- ✅ Pay-per-execution model
- ✅ Integrates directly with Static Web Apps

**Cons:**
- ❌ Requires rewriting all FastAPI code to Azure Functions format
- ❌ Cold start delays (first request can be slow)
- ❌ Different programming model

**Best for**: Event-driven apps, APIs with sporadic traffic, or if already using Azure Functions

**Not recommended for your case**: Too much refactoring required

---

#### Option 4: Azure Container Apps

**What it is**: Managed container service (simplified Kubernetes)

**Pros:**
- ✅ Can scale to zero (save money on low-traffic apps)
- ✅ Full Docker flexibility
- ✅ Advanced auto-scaling (0 to 100+ instances)
- ✅ Good for microservices

**Cons:**
- ❌ Requires Docker knowledge
- ❌ More expensive (~$30-50/month if always running)
- ❌ More complex setup (Dockerfile, Container Registry, deployment)
- ❌ Overkill for simple apps

**Best for**: Microservices architectures, need advanced scaling, already have Docker expertise

**Is it Kubernetes?** Sort of! Container Apps runs on Kubernetes but hides the complexity:
- **Azure Kubernetes Service (AKS)**: Full Kubernetes, you manage everything (complex, ~$70+/month)
- **Container Apps**: Kubernetes under the hood, but Azure abstracts it away (easier than AKS, harder than App Service)

**Not recommended for your case**: Too complex and expensive for a simple FastAPI app

---

### Recommended: Deploy Backend to Azure App Service (Option 2)

#### Prerequisites

1. **Azure CLI installed**: 
   ```powershell
   winget install Microsoft.AzureCLI
   ```

2. **Azure account with active subscription**

#### Step 1: Login to Azure

```powershell
az login
```

Your browser will open for authentication.

#### Step 2: Deploy Backend (One Command!)

```powershell
cd C:\Users\marku\Documents\2025\93_Project_AI\repos\asiaspanel\backend
az webapp up --name asiaspanel-backend --runtime PYTHON:3.11 --sku B1 --location eastus
```

This single command:
- Creates a resource group (if needed)
- Creates an App Service Plan (B1 tier)
- Creates the App Service
- Deploys your backend code
- Installs dependencies from `requirements.txt`

**Note**: The `--name` must be globally unique. If `asiaspanel-backend` is taken, try `asiaspanel-backend-yourname`.

#### Step 3: Configure Environment Variables

```powershell
az webapp config appsettings set --name asiaspanel-backend --settings OPENAI_API_KEY="your-openai-key-here"

az webapp config appsettings set --name asiaspanel-backend --settings AZURE_STORAGE_CONNECTION_STRING="your-azure-storage-connection-string"

az webapp config appsettings set --name asiaspanel-backend --settings AZURE_TTS_CONTAINER="tts-audio"
```

Replace the values with your actual keys.

#### Step 4: Get Your Backend URL

```powershell
az webapp show --name asiaspanel-backend --query defaultHostName -o tsv
```

Your backend URL will be: `https://asiaspanel-backend.azurewebsites.net`

#### Step 5: Test Backend

```powershell
curl https://asiaspanel-backend.azurewebsites.net/health
```

Should return: `{"status":"ok","uptime_seconds":...}`

#### Step 6: Enable CORS (Allow Frontend to Call Backend)

```powershell
az webapp cors add --name asiaspanel-backend --allowed-origins "https://proud-mud-09bc94003.azurestaticapps.net"
```

Replace with your actual Static Web App URL.

#### Step 7: Update Frontend to Use Production Backend

You need to update `index.html` to use the production backend URL when deployed. See "Update Frontend API Configuration" section below.

---

## Update Frontend API Configuration

After deploying the backend, update `asiaspanel-web2/index.html`:

**Option A: Auto-detect (Recommended)**

Replace this line:
```javascript
const API_BASE = '';// same origin: served by backend when running uvicorn
```

With:
```javascript
// Auto-detect: use production backend if running on Azure, otherwise local
const API_BASE = window.location.hostname.includes('azurestaticapps.net') 
  ? 'https://asiaspanel-backend.azurewebsites.net' 
  : '';
```

**Option B: Always use production backend**

```javascript
const API_BASE = 'https://asiaspanel-backend.azurewebsites.net';
```

Then commit and push to deploy the updated frontend:
```bash
git add asiaspanel-web2/index.html
git commit -m "Update frontend to use production backend"
git push origin master
```

---

## Environment Variables for Production

If you deploy the backend, configure these environment variables:

### Required:
- `OPENAI_API_KEY` - Your OpenAI API key for TTS

### Optional:
- `AZURE_STORAGE_CONNECTION_STRING` - Azure Blob Storage connection string
- `AZURE_TTS_CONTAINER` - Blob container name (default: `tts-audio`)
- `OPENAI_TTS_MODEL` - OpenAI TTS model (default: `tts-1`)

**These are already configured in Step 3 of the backend deployment above.**

---

## Workflow Configuration

The GitHub Actions workflow file is located at:
```
.github/workflows/azure-static-web-apps-proud-mud-09bc94003.yml
```

### Key Configuration:
```yaml
on:
  push:
    branches:
      - master  # Triggers on push to master

steps:
  - name: Build And Deploy
    with:
      app_location: "asiaspanel-web2"  # Frontend folder
      api_location: ""                  # Backend (currently empty)
      output_location: "."              # No build step, deploy as-is
```

---

## Troubleshooting

### Deployment Failed in GitHub Actions

**Check:**
1. View the Actions logs for specific error messages
2. Verify `app_location: "asiaspanel-web2"` matches your folder structure
3. Ensure Azure token secret is valid and not expired
4. Check if Azure Static Web App resource exists and is active

**Fix expired token:**
1. Go to Azure Portal → Static Web Apps → your app
2. Go to **Manage deployment token**
3. Copy the new token
4. Update GitHub secret `AZURE_STATIC_WEB_APPS_API_TOKEN_PROUD_MUD_09BC94003`

### Frontend Deployed But Features Don't Work

**Likely cause**: Backend is not deployed

**Solutions:**
- Deploy backend separately (see Backend Deployment Options)
- Update `API_BASE` in `index.html` to point to deployed backend URL
- Enable CORS in backend if frontend and backend are on different domains

### Changes Not Appearing on Production URL

**Check:**
1. Wait 2-3 minutes for CDN cache to update
2. Hard refresh browser: `Ctrl + F5`
3. Check if GitHub Actions job completed successfully
4. Verify you pushed to the correct branch (`master`)

### 404 Errors on Production

**Check:**
1. Verify files exist in `asiaspanel-web2/` folder
2. Confirm `output_location: "."` is correct in workflow
3. Check browser console for missing file errors

---

## Rollback Procedure

If you need to rollback to a previous version:

### Option 1: Git Revert
```bash
# Find the commit to revert to
git log --oneline

# Revert to specific commit
git revert <commit-hash>
git push origin master
```

### Option 2: Redeploy Previous Commit
```bash
# Checkout previous commit
git checkout <previous-commit-hash>

# Force push (use with caution)
git push origin master --force
```

### Option 3: Azure Portal
1. Go to Azure Portal → Static Web Apps → your app
2. Go to **Deployment history**
3. Select a previous deployment and promote it

---

## Quick Reference

**Deploy to production:**
```bash
git add .
git commit -m "Your changes"
git push origin master
```

**Check deployment status:**
- GitHub: `https://github.com/markuskoenig271/asiaspanel/actions`

**Production URL:**
- Frontend: `https://proud-mud-09bc94003.azurestaticapps.net` (or similar)
- Backend: Not deployed (requires manual setup)

**Local testing before deploy:**
```bash
scripts\run_local.bat
# Open http://localhost:8001 in browser
```

---

## Next Steps

To enable full production functionality:

1. ✅ Frontend deployment is automated
2. ⏳ Backend deployment needs to be set up (choose Option 2, 3, or 4)
3. ⏳ Configure production environment variables
4. ⏳ Update frontend API_BASE to point to production backend
5. ⏳ Set up custom domain (optional)
6. ⏳ Enable monitoring/logging (Application Insights)

---

**Last Updated**: November 29, 2025

---

## 📋 QUICK REFERENCE - Complete Deployment Steps

### Part 1: Frontend Deployment (Automatic via GitHub Actions)

#### Steps:

1. **Commit changes**
   ```bash
   git add .
   git commit -m "Add voice recording and file logging features"
   ```

2. **Push to master**
   ```bash
   git push origin master
   ```

3. **Monitor deployment**
   - Go to: https://github.com/markuskoenig271/asiaspanel/actions
   - Wait for "Azure Static Web Apps CI/CD" to complete (~1-3 minutes)

4. **Get production URL**
   ```powershell
   az staticwebapp show --name asiaspanel --resource-group <RESOURCE_GROUP> --query defaultHostname -o tsv
   ```
   Or check GitHub Actions output or Azure Portal

5. **Verify frontend**
   - Open production URL (e.g., `https://proud-mud-09bc94003.azurestaticapps.net`)
   - Verify page loads correctly

---

### Part 2: Backend Deployment (Azure App Service - Option 2)

#### Prerequisites:
```powershell
# Install Azure CLI (if not installed)
winget install Microsoft.AzureCLI

# Login to Azure
az login
```

#### Steps:

1. **Deploy backend (one command)**
   ```powershell
   cd C:\Users\marku\Documents\2025\93_Project_AI\repos\asiaspanel\backend
   az webapp up --name asiaspanel-backend --runtime PYTHON:3.11 --sku B1 --location eastus
   ```
   Note: If name is taken, try `asiaspanel-backend-yourname`

2. **Configure environment variables**
   ```powershell
   az webapp config appsettings set --name asiaspanel-backend --settings OPENAI_API_KEY="your-openai-key-here"
   
   az webapp config appsettings set --name asiaspanel-backend --settings AZURE_STORAGE_CONNECTION_STRING="your-connection-string"
   
   az webapp config appsettings set --name asiaspanel-backend --settings AZURE_TTS_CONTAINER="tts-audio"
   ```

3. **Get backend URL**
   ```powershell
   az webapp show --name asiaspanel-backend --query defaultHostName -o tsv
   ```
   Result: `https://asiaspanel-backend.azurewebsites.net`

4. **Test backend**
   ```powershell
   curl https://asiaspanel-backend.azurewebsites.net/health
   ```
   Expected: `{"status":"ok","uptime_seconds":...}`

5. **Enable CORS (allow frontend to call backend)**
   ```powershell
   az webapp cors add --name asiaspanel-backend --allowed-origins "https://proud-mud-09bc94003.azurestaticapps.net"
   ```
   (Replace with your actual Static Web App URL)

6. **Update frontend API configuration**
   
   Edit `asiaspanel-web2/index.html`, find:
   ```javascript
   const API_BASE = '';
   ```
   
   Replace with:
   ```javascript
   const API_BASE = window.location.hostname.includes('azurestaticapps.net') 
     ? 'https://asiaspanel-backend.azurewebsites.net' 
     : '';
   ```

7. **Deploy updated frontend**
   ```bash
   git add asiaspanel-web2/index.html
   git commit -m "Connect frontend to production backend"
   git push origin master
   ```

8. **Verify full deployment**
   - Open production frontend URL
   - Test TTS feature (should call production backend)
   - Test voice recording feature
   - Test translate feature
   - Check replay button works

---

### Summary

**Frontend URL**: `https://proud-mud-09bc94003.azurestaticapps.net` (or your actual URL)  
**Backend URL**: `https://asiaspanel-backend.azurewebsites.net`  
**Cost**: ~$13/month (B1 tier) or Free (F1 tier for testing)  
**Deployment time**: ~5-10 minutes total

---

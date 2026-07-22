# Azure Deployment Guide: SDGNY Photo Upload System v2.0

This guide outlines step-by-step instructions for deploying the **SDGNY Photo Upload System v2.0** to **Azure App Service**.

---

## 📋 Prerequisites
1. **Azure Subscription** with permissions to create App Services & Key Vaults / Application Settings.
2. **Azure CLI** installed locally (`az --version`) or use Azure Cloud Shell.
3. **ODBC Driver 17 for SQL Server** (Pre-installed on Azure Linux App Service Python runtime).
4. Required Environment Credentials:
   - **Azure SQL**: `DB_SERVER`, `DB_NAME`, `DB_USERNAME`, `DB_PASSWORD`, `DB_DRIVER`
   - **Procore API**: `PROCORE_CLIENT_ID`, `PROCORE_CLIENT_SECRET`
   - **SharePoint / MS Graph**: `TENANT_ID`, `CLIENT_ID`, `CLIENT_SECRET`

---

## 🚀 Recommended Deployment Option: Unified Azure App Service

In this architecture, FastAPI serves both the REST API endpoints (`/api/...`) and the compiled static React frontend assets from `frontend/dist`. This eliminates CORS issues and simplifies infrastructure into a single Azure App Service instance.

### Step 1: Update FastAPI to Serve Production Frontend Build

In `backend/app/main.py`, mount the production static build folder if it exists:

```python
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(title="SDGNY Photo Upload API")

# Include Routers
# app.include_router(...)

# Serve Static Frontend in Production
DIST_DIR = os.path.join(os.path.dirname(__file__), "../../frontend/dist")
if os.path.exists(DIST_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        if full_path.startswith("api"):
            return None
        file_path = os.path.join(DIST_DIR, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(DIST_DIR, "index.html"))
```

---

### Step 2: Build the Production Frontend

Run the Vite build command locally or in your CI/CD pipeline:

```bash
cd frontend
npm install
npm run build
```
This generates the optimized static bundle in `frontend/dist`.

---

### Step 3: Create Startup Script for Azure App Service

Create a file named `startup.sh` in the `backend` directory:

```bash
#!/bin/bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

---

### Step 4: Provision Azure App Service via Azure CLI

```bash
# 1. Login to Azure
az login

# 2. Create Resource Group
az group create --name rg-sdgny-photo-upload --location eastus

# 3. Create App Service Plan (B1 Basic or P1v2 Recommended)
az appservice plan create \
  --name plan-sdgny-upload \
  --resource-group rg-sdgny-photo-upload \
  --sku B1 \
  --is-linux

# 4. Create Web App (Python 3.12 Runtime)
az webapp create \
  --resource-group rg-sdgny-photo-upload \
  --plan plan-sdgny-upload \
  --name sdgny-photo-upload-app \
  --runtime "PYTHON:3.12"
```

---

### Step 5: Configure Application Settings (Environment Variables)

Set all backend secrets in Azure App Service Configuration:

```bash
az webapp config appsettings set \
  --resource-group rg-sdgny-photo-upload \
  --name sdgny-photo-upload-app \
  --settings \
    DB_SERVER="dw-sqldb.database.windows.net" \
    DB_NAME="dw-sqldb" \
    DB_USERNAME="your_sql_user" \
    DB_PASSWORD="your_sql_password" \
    DB_DRIVER="ODBC Driver 17 for SQL Server" \
    PROCORE_CLIENT_ID="your_procore_id" \
    PROCORE_CLIENT_SECRET="your_procore_secret" \
    TENANT_ID="your_azure_tenant_id" \
    CLIENT_ID="your_azure_client_id" \
    CLIENT_SECRET="your_azure_client_secret"
```

Set the custom startup command:
```bash
az webapp config set \
  --resource-group rg-sdgny-photo-upload \
  --name sdgny-photo-upload-app \
  --startup-file "startup.sh"
```

---

### Step 6: Deploy Code to Azure

Deploy via Zip Deploy or GitHub Actions CI/CD:

```bash
# Create zip deployment package
zip -r deploy.zip backend/ frontend/dist/ startup.sh

# Deploy to Azure Web App
az webapp deployment source config-zip \
  --resource-group rg-sdgny-photo-upload \
  --name sdgny-photo-upload-app \
  --src deploy.zip
```

---

## 🌐 Alternative Option 2: Split Deployment (App Service + Static Web Apps)

If you prefer keeping Frontend and Backend decoupled:

1. **Backend**: Deploy `backend/` to **Azure App Service (Python 3.12)** as described above. Set CORS origins to allow the frontend URL.
2. **Frontend**: Deploy `frontend/` to **Azure Static Web Apps** (Free Tier). Connect your GitHub repository (`main` branch) and set App Location to `/frontend` and Output Location to `dist`.

---

## 🔒 Security Best Practices for Azure Production
1. **Azure Key Vault Integration**: Store `DB_PASSWORD`, `CLIENT_SECRET`, and `PROCORE_CLIENT_SECRET` in Azure Key Vault and reference them via App Service Key Vault references (`@Microsoft.KeyVault(...)`).
2. **Managed Identity**: Enable System-Assigned Managed Identity on Azure App Service to authenticate to Azure SQL without hardcoded passwords.
3. **ODBC Driver Verification**: Azure App Service Linux containers include `ODBC Driver 17 for SQL Server` by default.

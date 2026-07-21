# Project Image Upload System v2.0

React + FastAPI refactor of the Streamlit upload app.

## What It Does

| Tab | Upload Destination | Data Source |
|---|---|---|
| Procore Projects | Procore API → SharePoint `Procore_Projects/{project_number}/{status}` | Live Procore API |
| Shopify Orders | SharePoint `Shopify_orders_photos/{CustomerName}/{OrderID}/{Status}` | Azure SQL `ShopifyProjectData` |
| Special Projects | SharePoint `Procore_Special_Projects_Photos/{ProjectCode}/{JobYear} Projects/{JobNumber}/{Status}` | Azure SQL `ProcoreProjectData` (letter-prefix rows) |

## Folder Structure

```
Photo-upload App (2.0)/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI app + CORS + health endpoint
│   │   ├── config.py             # Pydantic settings from .env
│   │   ├── routers/
│   │   │   ├── procore.py        # GET /api/procore/projects, POST /api/procore/upload
│   │   │   ├── shopify.py        # GET /api/shopify/orders, POST /api/shopify/upload
│   │   │   └── special.py        # GET /api/special/projects, POST /api/special/upload
│   │   └── services/
│   │       ├── procore_client.py # Procore OAuth2 + API calls
│   │       ├── sharepoint.py     # MSAL + Microsoft Graph uploads
│   │       ├── database.py       # Azure SQL queries
│   │       └── image_utils.py    # PIL image optimizer + EXIF stripper
│   ├── uploads/                  # Temp staging (auto-created, auto-cleaned)
│   ├── .env                      # Secrets (fill in passwords)
│   ├── requirements.txt
│   └── run.py
└── frontend/
    ├── public/logo.jpg
    ├── src/
    │   ├── api/client.js         # Axios API functions
    │   ├── components/           # Header, TabNav, FileDropzone, UploadProgress
    │   └── pages/                # ProcoreProjects, ShopifyOrders, SpecialProjects
    └── vite.config.js            # Proxy /api → localhost:8000
```

## Setup

### 1. Fill in backend/.env
Open `backend/.env` and replace the placeholder passwords with real values.

### 2. Backend
```bash
cd backend
pip install -r requirements.txt
python run.py
# → http://localhost:8000
# → Swagger docs: http://localhost:8000/docs
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | DB connection status |
| GET | `/api/procore/projects` | List all Procore projects |
| POST | `/api/procore/upload` | Upload to Procore + SharePoint |
| GET | `/api/shopify/orders` | List order IDs + customer names |
| POST | `/api/shopify/upload` | Upload to SharePoint Shopify drive |
| GET | `/api/special/projects` | List special projects from Azure SQL |
| POST | `/api/special/upload` | Upload to SharePoint Special Projects drive |

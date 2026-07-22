import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.routers import procore, shopify, special
from app.services.database import test_connection

app = FastAPI(title="Photo Upload API", version="2.0.0")

# Allow the Vite dev server and any future production origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(procore.router)
app.include_router(shopify.router)
app.include_router(special.router)


@app.get("/api/health")
def health():
    """Check database connectivity."""
    db_ok, db_msg = test_connection()
    return {
        "database": {"ok": db_ok, "message": db_msg},
    }


# ---------------------------------------------------------------------------
# Unified Deployment: Serve Production React Frontend Build (frontend/dist)
# ---------------------------------------------------------------------------
DIST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist"))

if os.path.exists(DIST_DIR):
    assets_dir = os.path.join(DIST_DIR, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        # Do not catch API routes
        if full_path.startswith("api"):
            return None
        file_path = os.path.join(DIST_DIR, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(DIST_DIR, "index.html"))


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import procore, shopify, special
from app.services.database import test_connection

app = FastAPI(title="Photo Upload API", version="2.0.0")

# Allow the Vite dev server and any future production origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://[::1]:5173",
    ],
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

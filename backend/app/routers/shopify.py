import os

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.services import sharepoint
from app.services.database import get_all_shopify_orders
from app.services.image_utils import optimize_image

router = APIRouter(prefix="/api/shopify", tags=["shopify"])

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "tif", "tiff", "pdf"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}
STATUS_OPTIONS = ["PRODUCTION", "SHIPPED", "PICKUP", "INSTALLATION", "SITE SURVEY"]
PERSON_NAMES = [
    "Muhammad", "Mikhail", "Sid", "Alex", "Kathy", "Luis",
    "Genesis", "Elias", "Edgar", "Ivan", "Yolani", "Rafa",
    "Alma", "Maritza", "Jason",
]

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@router.get("/orders")
def list_orders():
    """
    Return all Shopify order IDs and their customer names from Azure SQL.
    Returns: [{"order_id": "1234", "customer_name": "John Doe"}, ...]
    """
    return get_all_shopify_orders()


@router.post("/upload")
async def upload_shopify(
    order_id: str = Form(...),
    customer_name: str = Form(...),
    status: str = Form(...),
    person_name: str = Form(...),
    files: list[UploadFile] = File(...),
):
    """
    Upload images to SharePoint under:
      Shopify_orders_photos / {CustomerName} / {OrderID} / {Status}

    Flow (mirrors shopify_upload_tab() exactly):
    1. Get SharePoint token
    2. Resolve drive + folder path
    3. For each file: optimize if image, save to disk, upload, delete local file
    """
    if status not in STATUS_OPTIONS:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    if person_name not in PERSON_NAMES:
        raise HTTPException(status_code=400, detail=f"Invalid person name: {person_name}")

    # Step 1: SharePoint auth + folder resolution
    token, err = sharepoint.get_access_token()
    if err:
        raise HTTPException(status_code=502, detail=f"SharePoint auth failed: {err}")

    drive_id, err = sharepoint.get_drive_id(token, sharepoint.DRIVE_SHOPIFY_ORDERS)
    if err:
        raise HTTPException(status_code=502, detail=f"Could not locate SharePoint drive: {err}")

    folder_path = f"{customer_name}/{order_id}/{status}"
    folder_id, err = sharepoint.get_or_create_folder_path(token, drive_id, folder_path)
    if err:
        raise HTTPException(status_code=502, detail=f"Could not create folder path: {err}")

    # Step 2: Process and upload each file
    success_count = 0
    errors: list[str] = []

    for uploaded_file in files:
        original_name = os.path.splitext(uploaded_file.filename)[0]
        ext = os.path.splitext(uploaded_file.filename)[1]
        file_name = f"{original_name}_{person_name}{ext}"
        file_path = os.path.join(UPLOAD_FOLDER, file_name)

        file_bytes = await uploaded_file.read()
        file_size_mb = len(file_bytes) / (1024 * 1024)
        ext_lower = ext.lower()

        # Optimize images (more aggressive for files > 20 MB)
        if ext_lower in IMAGE_EXTENSIONS:
            if file_size_mb > 20:
                file_bytes = optimize_image(
                    file_bytes, max_size=1600, quality=75, max_file_size_mb=19
                )
            else:
                file_bytes = optimize_image(file_bytes, max_file_size_mb=19)

        # Save to disk then upload (avoids stream issues)
        try:
            with open(file_path, "wb") as fh:
                fh.write(file_bytes)

            with open(file_path, "rb") as fh:
                content = fh.read()

            _, error = sharepoint.upload_bytes(token, drive_id, folder_id, file_name, content)
            if error:
                errors.append(f"Failed to upload {file_name}: {error}")
            else:
                success_count += 1
        except Exception as e:
            errors.append(f"Error processing {file_name}: {e}")
        finally:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass

    return {
        "success_count": success_count,
        "total": len(files),
        "errors": errors,
    }

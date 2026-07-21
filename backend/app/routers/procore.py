import os
import uuid
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.services import sharepoint
from app.services.image_utils import strip_exif_and_repack
from app.services.procore_client import ProcoreClient

router = APIRouter(prefix="/api/procore", tags=["procore"])

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "tif", "tiff", "pdf"}
STATUS_OPTIONS = ["PRODUCTION", "SHIPPED", "PICKUP", "INSTALLATION", "SITE SURVEY"]
PERSON_NAMES = [
    "Muhammad", "Mikhail", "Sid", "Alex", "Kathy", "Luis",
    "Genesis", "Elias", "Edgar", "Ivan", "Yolani", "Rafa",
    "Alma", "Maritza", "Jason",
]

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@router.get("/projects")
def list_projects():
    """
    Fetch all active Procore projects.
    Returns: [{"id": 123, "name": "...", "number": "101"}, ...]
    """
    client = ProcoreClient()
    projects = client.list_projects()
    if not projects:
        raise HTTPException(status_code=502, detail="Could not fetch projects from Procore API")
    return projects


@router.post("/upload")
async def upload_to_procore(
    project_id: int = Form(...),
    project_number: str = Form(...),
    status: str = Form(...),
    person_name: str = Form(...),
    files: list[UploadFile] = File(...),
):
    """
    Upload images to Procore and back them up to SharePoint.

    Flow (mirrors streamlit_app_cloud.py exactly):
    1. Ensure album exists in Procore for the selected status
    2. Strip EXIF + upload each file to Procore in parallel (5 workers)
    3. Back up successfully uploaded files to SharePoint Procore_Projects drive
    4. Clean up local temp files
    """
    if status not in STATUS_OPTIONS:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    if person_name not in PERSON_NAMES:
        raise HTTPException(status_code=400, detail=f"Invalid person name: {person_name}")

    client = ProcoreClient()

    # Step 1: Ensure album exists
    album_id, error = client.ensure_album_exists(project_id, status)
    if not album_id:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to find/create album '{status}' in Procore: {error}",
        )

    # Read all file bytes upfront (UploadFile stream can only be read once)
    file_payloads = []
    for f in files:
        ext = os.path.splitext(f.filename)[1].lower().lstrip(".")
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"File type .{ext} not allowed")
        content = await f.read()
        file_payloads.append((f.filename, ext, content))

    saved_paths: list[str] = []
    errors: list[str] = []

    # Step 2: Strip EXIF + upload to Procore in parallel
    def upload_worker(payload):
        original_name, ext, file_bytes = payload
        unique_filename = f"{status}_{uuid.uuid4()}_{person_name}.{ext}"

        # Strip EXIF for image types
        if ext in ("jpg", "jpeg", "png"):
            file_bytes = strip_exif_and_repack(file_bytes, unique_filename)

        success, resp = client.upload_photo(project_id, album_id, file_bytes, unique_filename)
        if success:
            # Save locally for SharePoint backup
            path = os.path.join(UPLOAD_FOLDER, unique_filename)
            with open(path, "wb") as fh:
                fh.write(file_bytes)
            return True, path
        return False, f"Procore upload failed for {original_name}: {resp}"

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(upload_worker, file_payloads))

    for success, result in results:
        if success:
            saved_paths.append(result)
        else:
            errors.append(result)

    success_count = len(saved_paths)

    if success_count == 0:
        raise HTTPException(status_code=502, detail="No images were uploaded to Procore")

    # Step 3: SharePoint backup
    sp_errors: list[str] = []
    token, err = sharepoint.get_access_token()
    if token:
        drive_id, err = sharepoint.get_drive_id(token, sharepoint.DRIVE_PROCORE_PROJECTS)
        if drive_id:
            folder_path = f"{project_number}/{status}"
            folder_id, err = sharepoint.get_or_create_folder_path(token, drive_id, folder_path)
            if folder_id:
                def sp_worker(file_path):
                    file_name = os.path.basename(file_path)
                    _, error = sharepoint.upload_file(token, drive_id, folder_id, file_path, file_name)
                    return error

                with ThreadPoolExecutor(max_workers=5) as sp_executor:
                    sp_results = list(sp_executor.map(sp_worker, saved_paths))

                sp_errors = [e for e in sp_results if e]

    # Step 4: Cleanup temp files
    for path in saved_paths:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

    return {
        "success_count": success_count,
        "total": len(file_payloads),
        "errors": errors + sp_errors,
    }

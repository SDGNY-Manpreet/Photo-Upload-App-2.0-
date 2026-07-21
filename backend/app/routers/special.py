import os
from datetime import datetime

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.services import sharepoint
from app.services.database import get_all_special_projects
from app.services.image_utils import optimize_image

router = APIRouter(prefix="/api/special", tags=["special"])

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


def _extract_project_code(project_id: str) -> str:
    """
    'BCHS 2025' → 'BCHS'
    Strips trailing year token if the last part is all digits.
    Exact port of extract_project_code() from streamlit_app_cloud.py.
    """
    parts = project_id.split()
    if len(parts) >= 2 and parts[-1].isdigit():
        return " ".join(parts[:-1])
    return project_id


def _extract_year_from_job_number(job_number: str) -> str:
    """
    '25-1234' → '2025'
    Exact port of extract_year_from_job_number() from streamlit_app_cloud.py.
    """
    if "-" in job_number:
        prefix = job_number.split("-")[0]
        if prefix.isdigit() and len(prefix) == 2:
            return f"20{prefix}"
    return str(datetime.now().year)


@router.get("/projects")
def list_special_projects():
    """
    Return special project IDs (starting with letters) from Azure SQL,
    including project name and customer.
    Returns: [{"project_number": "BCHS 2025", "project_name": "...", "customer": "..."}, ...]
    """
    return get_all_special_projects()


@router.post("/upload")
async def upload_special(
    project_id: str = Form(...),
    job_number: str = Form(...),
    status: str = Form(...),
    person_name: str = Form(...),
    files: list[UploadFile] = File(...),
):
    """
    Upload images to SharePoint under:
      Procore_Special_Projects_Photos / {ProjectCode} / {JobYear} Projects / {JobNumber} / {Status}

    Flow (mirrors special_projects_tab() exactly):
    1. Parse project_code from project_id and job_year from job_number
    2. Get SharePoint token + resolve folder path
    3. For each file: optimize if image, save to disk, upload, delete local file
    """
    if not job_number.strip():
        raise HTTPException(status_code=400, detail="Job number is required")
    if status not in STATUS_OPTIONS:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    if person_name not in PERSON_NAMES:
        raise HTTPException(status_code=400, detail=f"Invalid person name: {person_name}")

    project_code = _extract_project_code(project_id)
    job_year = _extract_year_from_job_number(job_number)

    # Step 1: SharePoint auth + folder resolution
    token, err = sharepoint.get_access_token()
    if err:
        raise HTTPException(status_code=502, detail=f"SharePoint auth failed: {err}")

    drive_id, err = sharepoint.get_drive_id(token, sharepoint.DRIVE_SPECIAL_PROJECTS)
    if err:
        raise HTTPException(status_code=502, detail=f"Could not locate SharePoint drive: {err}")

    folder_path = f"{project_code}/{job_year} Projects/{job_number}/{status}"
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

        if ext_lower in IMAGE_EXTENSIONS:
            if file_size_mb > 20:
                file_bytes = optimize_image(
                    file_bytes, max_size=1600, quality=75, max_file_size_mb=19
                )
            else:
                file_bytes = optimize_image(file_bytes, max_file_size_mb=19)

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

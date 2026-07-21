import msal
import requests
from app.config import settings

# SharePoint drive names — exactly as in the original app
DRIVE_PROCORE_PROJECTS = "Procore_Projects"
DRIVE_SHOPIFY_ORDERS = "Shopify_orders_photos"
DRIVE_SPECIAL_PROJECTS = "Procore_Special_Projects_Photos"


def get_access_token() -> tuple[str | None, str | None]:
    """
    Acquire a Microsoft Graph API token using MSAL client credentials.
    Token is valid ~60 minutes; callers should cache it themselves if needed.
    Returns (token, error).
    """
    try:
        app = msal.ConfidentialClientApplication(
            client_id=settings.sharepoint_client_id,
            client_credential=settings.sharepoint_client_secret,
            authority=f"https://login.microsoftonline.com/{settings.sharepoint_tenant_id}",
        )
        result = app.acquire_token_for_client(
            scopes=["https://graph.microsoft.com/.default"]
        )
        if "access_token" in result:
            return result["access_token"], None
        return None, result.get("error_description", "Unknown MSAL error")
    except Exception as e:
        return None, str(e)


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def get_drive_id(token: str, drive_name: str) -> tuple[str | None, str | None]:
    """Find a SharePoint drive by its display name. Returns (drive_id, error)."""
    try:
        res = requests.get(
            "https://graph.microsoft.com/v1.0/sites/root/drives",
            headers=_auth_headers(token),
        )
        if res.status_code == 200:
            for drive in res.json().get("value", []):
                if drive.get("name") == drive_name:
                    return drive.get("id"), None
            return None, f"Drive '{drive_name}' not found"
        return None, f"Failed to list drives: {res.status_code} - {res.text}"
    except Exception as e:
        return None, str(e)


def _get_or_create_single_folder(
    token: str, drive_id: str, parent_folder_id: str, folder_name: str
) -> tuple[str | None, str | None]:
    """Get existing folder or create it. Returns (folder_id, error)."""
    headers = _auth_headers(token)

    # Look for existing folder
    if parent_folder_id == "root":
        list_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root/children"
    else:
        list_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{parent_folder_id}/children"

    res = requests.get(list_url, headers=headers)
    if res.status_code == 200:
        for item in res.json().get("value", []):
            if item.get("name") == folder_name and "folder" in item:
                return item.get("id"), None

    # Create it
    if parent_folder_id == "root":
        create_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root/children"
    else:
        create_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{parent_folder_id}/children"

    payload = {
        "name": folder_name,
        "folder": {},
        "@microsoft.graph.conflictBehavior": "rename",
    }
    res = requests.post(create_url, headers=headers, json=payload)
    if res.status_code == 201:
        return res.json().get("id"), None
    return None, f"Failed to create folder '{folder_name}': {res.status_code} - {res.text}"


def get_or_create_folder_path(
    token: str, drive_id: str, folder_path: str
) -> tuple[str | None, str | None]:
    """
    Walk/create each level of a folder path (e.g. 'CustomerName/OrderID/Status').
    Returns (leaf_folder_id, error).
    """
    folders = [f for f in folder_path.strip("/").split("/") if f]
    current_id = "root"
    for folder_name in folders:
        current_id, error = _get_or_create_single_folder(token, drive_id, current_id, folder_name)
        if error:
            return None, error
    return current_id, None


def upload_file(
    token: str, drive_id: str, folder_id: str, file_path: str, file_name: str
) -> tuple[str | None, str | None]:
    """
    Upload a file from disk to SharePoint.
    Returns (web_url, error).
    """
    try:
        with open(file_path, "rb") as f:
            file_content = f.read()

        headers = {"Authorization": f"Bearer {token}"}
        if folder_id == "root":
            url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{file_name}:/content"
        else:
            url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{folder_id}:/{file_name}:/content"

        res = requests.put(url, headers=headers, data=file_content)
        if res.status_code in (200, 201):
            return res.json().get("webUrl"), None
        return None, f"Failed to upload file: {res.status_code} - {res.text}"
    except Exception as e:
        return None, str(e)


def upload_bytes(
    token: str, drive_id: str, folder_id: str, file_name: str, file_content: bytes
) -> tuple[str | None, str | None]:
    """
    Upload raw bytes directly to SharePoint (used by Shopify + Special Projects).
    Returns (web_url, error).
    """
    try:
        headers = {"Authorization": f"Bearer {token}"}
        if folder_id == "root":
            url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{file_name}:/content"
        else:
            url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{folder_id}:/{file_name}:/content"

        res = requests.put(url, headers=headers, data=file_content)
        if res.status_code in (200, 201):
            return res.json().get("webUrl"), None
        return None, f"Failed to upload file: {res.status_code} - {res.text}"
    except Exception as e:
        return None, str(e)

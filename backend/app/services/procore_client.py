import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from app.config import settings


class ProcoreClient:
    """
    Handles Procore OAuth2 (client_credentials) and all API calls
    needed by the upload app:
      - list_projects()
      - ensure_album_exists()
      - upload_photo()
    """

    def __init__(self):
        self.client_id = settings.procore_client_id
        self.client_secret = settings.procore_client_secret
        self.base_url = settings.procore_base_url
        self.token_url = settings.procore_token_url
        self.token: str | None = None
        self.company_id: int | None = None

        # Robust retry session — same as original procore_api.py
        self.session = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        self.session.mount("http://", HTTPAdapter(max_retries=retries))

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def authenticate(self) -> bool:
        """Exchange client credentials for a Bearer token."""
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        try:
            res = self.session.post(self.token_url, json=payload)
            if res.status_code == 200:
                self.token = res.json()["access_token"]
                return True
            return False
        except Exception:
            return False

    def _ensure_token(self):
        if not self.token:
            self.authenticate()

    def _resolve_company_id(self):
        """Fetch and cache the first company ID for production Procore."""
        if self.company_id:
            return
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            res = self.session.get(f"{self.base_url}companies", headers=headers)
            if res.status_code == 200:
                companies = res.json()
                if companies:
                    self.company_id = companies[0]["id"]
        except Exception:
            pass

    def _json_headers(self) -> dict:
        self._ensure_token()
        self._resolve_company_id()
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        if self.company_id:
            headers["Procore-Company-Id"] = str(self.company_id)
        return headers

    def _upload_headers(self) -> dict:
        """Headers for multipart uploads — no Content-Type (requests sets boundary)."""
        self._ensure_token()
        self._resolve_company_id()
        headers = {"Authorization": f"Bearer {self.token}"}
        if self.company_id:
            headers["Procore-Company-Id"] = str(self.company_id)
        return headers

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------

    def list_projects(self) -> list[dict]:
        """
        Returns all projects for the company, paginated.
        Each item: {'id': int, 'name': str, 'number': str}
        """
        headers = self._json_headers()
        if not self.company_id:
            return []

        projects = []
        page = 1
        while True:
            res = self.session.get(
                f"{self.base_url}projects?company_id={self.company_id}&page={page}&per_page=100",
                headers=headers,
            )
            if res.status_code != 200:
                break
            data = res.json()
            if not data:
                break
            for p in data:
                projects.append(
                    {
                        "id": p.get("id"),
                        "name": p.get("name", "Unknown"),
                        "number": str(p.get("project_number") or "No #"),
                    }
                )
            if len(data) < 100:
                break
            page += 1

        return projects

    # ------------------------------------------------------------------
    # Albums (Image Categories)
    # ------------------------------------------------------------------

    def _get_album_by_name(self, project_id: int, name: str) -> tuple[int | None, str | None]:
        res = self.session.get(
            f"{self.base_url}image_categories?project_id={project_id}",
            headers=self._json_headers(),
        )
        if res.status_code == 200:
            for album in res.json():
                if album["name"] == name:
                    return album["id"], None
        return None, None

    def _create_album(self, project_id: int, name: str) -> tuple[int | None, str | None]:
        res = self.session.post(
            f"{self.base_url}image_categories?project_id={project_id}",
            headers=self._json_headers(),
            json={"image_category": {"name": name}},
        )
        if res.status_code in (200, 201):
            return res.json()["id"], None
        return None, f"Failed to create album '{name}': {res.status_code} - {res.text}"

    def ensure_album_exists(self, project_id: int, status_name: str) -> tuple[int | None, str | None]:
        """Get or create an album by name. Returns (album_id, error)."""
        if not status_name:
            status_name = "Unclassified"
        album_id, _ = self._get_album_by_name(project_id, status_name)
        if album_id:
            return album_id, None
        return self._create_album(project_id, status_name)

    # ------------------------------------------------------------------
    # Upload
    # ------------------------------------------------------------------

    def upload_photo(
        self, project_id: int, album_id: int, file_bytes: bytes, filename: str
    ) -> tuple[bool, object]:
        """Upload a photo to a Procore project album. Returns (success, response)."""
        url = f"{self.base_url}images?project_id={project_id}"
        files = {"image[data]": (filename, file_bytes, "image/jpeg")}
        data = {"image[name]": filename}
        if album_id:
            data["image[image_category_id]"] = str(album_id)

        try:
            res = self.session.post(url, headers=self._upload_headers(), files=files, data=data)
            if res.status_code in (200, 201):
                return True, res.json()
            return False, res.text
        except Exception as e:
            return False, str(e)

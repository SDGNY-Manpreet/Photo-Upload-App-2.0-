import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import toml
import os
import io

class ProcoreAPI:
    """
    Helper class for creating and managing Procore API interactions.
    Handles authentication, project listing, album management, and photo uploads.
    """
    BASE_URL = "https://sandbox.procore.com/rest/v1.0/"
    TOKEN_URL = "https://login-sandbox.procore.com/oauth/token"
    
    def __init__(self, secrets_path=".streamlit/secrets.toml"):
        self.secrets_path = secrets_path
        self.token = None
        self.client_id = None
        self.client_secret = None
        self.base_url = self.BASE_URL
        self.token_url = self.TOKEN_URL
        self.company_id = None
        
        self.session = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        self.session.mount("http://", HTTPAdapter(max_retries=retries))
        
        self.load_secrets()

    def load_secrets(self):
        try:
            with open(self.secrets_path, "r") as f:
                secrets = toml.load(f)["procore"]
            self.client_id = secrets["client_id"]
            self.client_secret = secrets["client_secret"]
            
            if "base_url" in secrets:
                self.base_url = secrets["base_url"]
            if "token_url" in secrets:
                self.token_url = secrets["token_url"]
                
        except Exception as e:
            # Fallback to environment variables
            self.client_id = os.getenv("PROCORE_CLIENT_ID", "")
            self.client_secret = os.getenv("PROCORE_CLIENT_SECRET", "")
            self.base_url = os.getenv("PROCORE_BASE_URL", self.BASE_URL)
            self.token_url = os.getenv("PROCORE_TOKEN_URL", self.TOKEN_URL)

    def authenticate(self):
        payload = {
            "grant_type": "client_credentials", 
            "client_id": self.client_id, 
            "client_secret": self.client_secret
        }
        try:
            res = self.session.post(self.token_url, json=payload)
            if res.status_code == 200:
                self.token = res.json()["access_token"]
                return True
            else:
                return False
        except Exception:
            return False

    def get_headers(self):
        if not self.token:
            self.authenticate()
        
        if not self.company_id and "sandbox" not in self.base_url:
            try:
                headers_simple = {"Authorization": f"Bearer {self.token}"}
                res = self.session.get(f"{self.base_url}companies", headers=headers_simple)
                if res.status_code == 200:
                    companies = res.json()
                    if companies:
                        self.company_id = companies[0]["id"]
            except Exception:
                pass

        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        if self.company_id:
            headers["Procore-Company-Id"] = str(self.company_id)
        return headers
        
    def get_upload_headers(self):
        base_h = self.get_headers()
        headers = {"Authorization": base_h["Authorization"]} 
        if self.company_id:
            headers["Procore-Company-Id"] = str(self.company_id)
        return headers

    def list_projects(self):
        headers = self.get_headers()
        
        try:
            if not self.company_id:
                simple_headers = {"Authorization": f"Bearer {self.token}"}
                res_c = self.session.get(f"{self.base_url}companies", headers=simple_headers)
                if res_c.status_code == 200:
                    companies = res_c.json()
                    if companies:
                        self.company_id = companies[0]['id']
                        headers = self.get_headers()

            if not self.company_id:
                return []
            
            projects_data = []
            page = 1
            while True:
                res_p = self.session.get(
                    f"{self.base_url}projects?company_id={self.company_id}&page={page}&per_page=100", 
                    headers=headers
                )
                if res_p.status_code != 200:
                    break
                    
                data = res_p.json()
                if not data:
                    break
                    
                for p in data:
                    p_id = p.get('id')
                    p_name = p.get('name', 'Unknown')
                    p_num = p.get('project_number') 
                    
                    if p_num is None:
                        p_num = "No #"
                        
                    projects_data.append({
                        'id': p_id,
                        'name': p_name,
                        'number': str(p_num)
                    })
                
                if len(data) < 100:
                    break
                page += 1
                
            return projects_data
            
        except Exception:
            return []

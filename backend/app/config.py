from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Procore
    procore_client_id: str
    procore_client_secret: str
    procore_base_url: str = "https://api.procore.com/rest/v1.0/"
    procore_token_url: str = "https://login.procore.com/oauth/token"

    # Azure SQL
    db_server: str
    db_name: str
    db_username: str
    db_password: str
    db_driver: str = "ODBC Driver 17 for SQL Server"

    # SharePoint (Microsoft Graph)
    sharepoint_client_id: str
    sharepoint_client_secret: str
    sharepoint_tenant_id: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

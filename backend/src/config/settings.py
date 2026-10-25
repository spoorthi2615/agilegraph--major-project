from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    app_name: str = "AgileGraph"
    env: str = "development"
    debug: bool = True
    port: int = 8000
    
    # Environment and Security
    agilegraph_env: Optional[str] = None
    agilegraph_secret_key: Optional[str] = None
    agilegraph_allow_anonymous: bool = False
    
    # Database and Storage
    database_url: str = "sqlite:///./agilegraph.db"
    agilegraph_auth_db: Optional[str] = None
    
    # Scanner & Heuristic Settings
    agilegraph_scan_root: Optional[str] = None
    allowed_scan_root: Optional[str] = None
    missing_data_policy: str = "RENORMALIZE"
    
    # OSV Vulnerability Intelligence
    osv_api_url: str = "https://api.osv.dev/v1/query"
    osv_timeout_seconds: float = 5.0
    
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

settings = Settings()

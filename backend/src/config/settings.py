from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    app_name: str = "AgileGraph"
    env: str = "development"
    debug: bool = True
    
    database_url: str = "sqlite:///./agilegraph.db"
    osv_api_url: str = "https://api.osv.dev/v1/query"
    osv_timeout_seconds: float = 5.0
    
    model_config = {"env_file": ".env"}

settings = Settings()

from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    app_name: str = "AgileGraph"
    env: str = "development"
    debug: bool = True
    
    neo4j_uri: Optional[str] = "bolt://localhost:7687"
    neo4j_user: Optional[str] = "neo4j"
    neo4j_password: Optional[str] = "secret"
    
    model_config = {"env_file": ".env"}

settings = Settings()

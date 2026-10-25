import os
import re
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from fastapi import Header, HTTPException, Depends
from src.core.logger import get_logger

logger = get_logger(__name__)

# Default dev fallback key (strictly forbidden in production)
DEFAULT_DEV_SECRET = "agilegraph-pqc-research-super-secret-key-2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

def is_production() -> bool:
    """Check if the current execution environment is flagged as production."""
    env_str = os.environ.get(
        "AGILEGRAPH_ENV", 
        os.environ.get("ENV", os.environ.get("ENVIRONMENT", ""))
    ).strip().lower()
    return env_str in ("production", "prod")

def get_secret_key() -> str:
    """
    Retrieve JWT signing secret key.
    
    SECURITY ENFORCEMENT:
    - In production, AGILEGRAPH_SECRET_KEY is strictly required, cannot be the default dev key,
      and must have a minimum length of 32 characters.
    - In development/testing, the default secret key is permitted with a warning.
    """
    secret = os.environ.get("AGILEGRAPH_SECRET_KEY")
    if is_production():
        if not secret or secret == DEFAULT_DEV_SECRET:
            raise RuntimeError(
                "CRITICAL SECURITY CONFIGURATION ERROR: A strong, unique AGILEGRAPH_SECRET_KEY "
                "environment variable is strictly required in production deployments. "
                "The default development key is not permitted in production."
            )
        if len(secret) < 32:
            raise RuntimeError(
                "CRITICAL SECURITY CONFIGURATION ERROR: AGILEGRAPH_SECRET_KEY in production "
                "must be at least 32 characters long."
            )
        return secret
    return secret or DEFAULT_DEV_SECRET

def is_anonymous_allowed() -> bool:
    """
    Check if anonymous development/testing override is permitted.
    
    SECURITY RULE:
    - Anonymous access is ONLY allowed when AGILEGRAPH_ALLOW_ANONYMOUS is explicitly set to '1'
      in a non-production environment (specifically for backward-compatible test suites).
    - It is NEVER allowed in production under any circumstances.
    """
    if is_production():
        if os.environ.get("AGILEGRAPH_ALLOW_ANONYMOUS") == "1":
            logger.critical(
                "SECURITY ALERT: AGILEGRAPH_ALLOW_ANONYMOUS=1 was detected in a production environment! "
                "Anonymous override is strictly disabled in production."
            )
        return False
    return os.environ.get("AGILEGRAPH_ALLOW_ANONYMOUS") == "1"

class User(BaseModel):
    id: str
    username: str
    email: str
    created_at: Optional[str] = None

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User

def hash_password(password: str) -> str:
    """Hash a plaintext password securely using bcrypt with 12 rounds."""
    # Bcrypt maximum password length is 72 bytes
    pw_bytes = password.encode("utf-8")
    if len(pw_bytes) > 72:
        raise ValueError("Password cannot exceed 72 bytes due to bcrypt limitation.")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(pw_bytes, salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    try:
        pw_bytes = plain_password.encode("utf-8")
        if len(pw_bytes) > 72:
            return False
        return bcrypt.checkpw(pw_bytes, hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generate a signed JWT access token using the active secret key."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    secret_key = get_secret_key()
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a signed JWT access token."""
    try:
        secret_key = get_secret_key()
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        return payload
    except (jwt.PyJWTError, Exception):
        return None

def get_current_user(authorization: Optional[str] = Header(None)) -> User:
    """
    FastAPI dependency to authenticate requests via Bearer token.
    
    Default behavior is SECURE:
    - Any missing, malformed, invalid, or revoked token raises HTTP 401 Unauthorized.
    - Anonymous access is only granted if is_anonymous_allowed() is True (dev/test override only).
    """
    from src.core.auth_storage import default_auth_storage

    if authorization:
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=401, 
                detail="Invalid authorization header format. Expected 'Bearer <token>'.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        token = authorization[7:].strip()
        if not token:
            raise HTTPException(
                status_code=401, 
                detail="Empty bearer token provided.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Check if token has been invalidated (logged out)
        if default_auth_storage.is_token_invalidated(token):
            raise HTTPException(
                status_code=401, 
                detail="Token has been revoked. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"}
            )
            
        payload = decode_access_token(token)
        if not payload or "sub" not in payload:
            raise HTTPException(
                status_code=401, 
                detail="Invalid or expired authentication token.",
                headers={"WWW-Authenticate": "Bearer"}
            )
            
        username = payload["sub"]
        user = default_auth_storage.get_user_by_username(username)
        if not user:
            raise HTTPException(
                status_code=401, 
                detail="User account no longer exists.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        return user

    # If no authorization header was provided:
    # Allow anonymous test user ONLY if explicitly enabled in environment AND not in production
    if is_anonymous_allowed():
        return User(
            id="anon_user_id",
            username="anonymous_test_user",
            email="anonymous@agilegraph.local",
            created_at=datetime.now(timezone.utc).isoformat()
        )

    # In standard mode, reject unauthenticated requests with 401
    raise HTTPException(
        status_code=401, 
        detail="Authentication required. Please provide a Bearer token in the Authorization header.",
        headers={"WWW-Authenticate": "Bearer"}
    )

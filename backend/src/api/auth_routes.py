import re
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional
from src.core.auth import (
    User,
    UserRegister,
    UserLogin,
    TokenResponse,
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)
from src.core.auth_storage import default_auth_storage

router = APIRouter(prefix="/auth", tags=["authentication"])

EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
USERNAME_REGEX = r"^[a-zA-Z0-9_\-\.]{3,30}$"

@router.post("/register", response_model=TokenResponse)
def register(req: UserRegister):
    username = req.username.strip().lower()
    email = req.email.strip().lower()
    password = req.password

    # Input validation
    if not re.match(USERNAME_REGEX, username):
        raise HTTPException(
            status_code=400,
            detail="Username must be 3-30 characters long and contain only letters, numbers, hyphens, and underscores."
        )

    if not re.match(EMAIL_REGEX, email):
        raise HTTPException(
            status_code=400,
            detail="Invalid email address format."
        )

    if len(password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters long."
        )

    if len(password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=400,
            detail="Password cannot exceed 72 bytes due to bcrypt limitation."
        )

    # Check for existing user
    if default_auth_storage.get_user_by_username(username):
        raise HTTPException(
            status_code=409,
            detail=f"Username '{username}' is already registered."
        )

    if default_auth_storage.get_user_by_email(email):
        raise HTTPException(
            status_code=409,
            detail=f"Email '{email}' is already registered."
        )

    # Hash password securely with bcrypt
    pw_hash = hash_password(password)
    user = default_auth_storage.create_user(username, email, pw_hash)

    # Generate JWT access token
    access_token = create_access_token({"sub": user.username, "email": user.email})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user
    )

@router.post("/login", response_model=TokenResponse)
def login(req: UserLogin):
    ident = req.username.strip().lower()
    password = req.password

    # Lookup user
    user = default_auth_storage.get_user_by_username(ident)
    if not user:
        user = default_auth_storage.get_user_by_email(ident)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Verify password hash
    stored_hash = default_auth_storage.get_user_password_hash(user.username)
    if not stored_hash or not verify_password(password, stored_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Generate JWT access token
    access_token = create_access_token({"sub": user.username, "email": user.email})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user
    )

@router.get("/me", response_model=User)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Retrieve the authenticated user's profile."""
    return current_user

@router.post("/logout")
def logout(authorization: Optional[str] = Header(None), current_user: User = Depends(get_current_user)):
    """Revoke the current session token."""
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
        default_auth_storage.invalidate_token(token)
    return {"message": "Logged out successfully."}

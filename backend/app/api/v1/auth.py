from fastapi import APIRouter, Depends, Request
from app.models.auth import LoginRequest, Token, User
from app.core.security import (
    verify_password,
    create_access_token,
    get_current_user_from_token
)
from app.core.exceptions import InvalidCredentialsException
from app.config import settings
from app.core.rate_limit import limiter

router = APIRouter()


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(request: Request, login_request: LoginRequest):
    """
    Login endpoint for UI operators.
    Returns JWT access token.
    """
    # Verify username and password
    # For now, we only support a single operator defined in env vars
    if login_request.username != settings.OPERATOR_USERNAME:
        raise InvalidCredentialsException()

    if not verify_password(login_request.password, settings.OPERATOR_PASSWORD_HASH):
        raise InvalidCredentialsException()

    # Create access token
    access_token = create_access_token(
        data={"sub": login_request.username}
    )

    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=User)
async def get_current_user(username: str = Depends(get_current_user_from_token)):
    """
    Get current authenticated user.
    Requires valid JWT token.
    """
    return User(username=username)

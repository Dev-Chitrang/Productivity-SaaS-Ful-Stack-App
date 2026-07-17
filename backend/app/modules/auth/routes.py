from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.core.config import settings
from app.core.database import get_db
from app.core.redis import get_redis_client
from app.core.cookies import set_refresh_cookie, delete_refresh_cookie
from app.modules.auth.repository import AuthRepository
from app.modules.auth.service import AuthService
from app.modules.auth.controller import AuthController
from app.modules.auth.schema import (
    UserRegisterRequest, OTPVerificationRequest, UserLoginRequest,
    TokenRefreshRequest, PasswordResetInitiate, PasswordResetConfirm,
    ResendOtpRequest, TokenResponse, GoogleOAuthRequest, GoogleOAuthResponse
)

from app.core.rate_limit import RateLimiter

router = APIRouter(prefix="/auth", tags=["Identity Operations Infrastructure"])

_IS_PROD = settings.ENVIRONMENT == "PRODUCTION"


async def get_controller(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis_client)
) -> AuthController:
    repo = AuthRepository(db)
    service = AuthService(repo, redis)
    return AuthController(service)


def _issue_tokens_response(response: Response, data: dict) -> dict:
    """Set refresh_token as HttpOnly cookie and return access_token body."""
    if data.get("refresh_token"):
        set_refresh_cookie(response, data["refresh_token"], is_production=_IS_PROD)
        data = {k: v for k, v in data.items() if k != "refresh_token"}
    return data


@router.post("/google", response_model=GoogleOAuthResponse, status_code=200, dependencies=[Depends(RateLimiter(3, 60, "auth"))])
async def google_oauth_route(
    payload: GoogleOAuthRequest,
    response: Response,
    ctrl: AuthController = Depends(get_controller),
):
    result = await ctrl.handle_google_oauth(payload)
    return _issue_tokens_response(response, result)


@router.post("/signup", status_code=201, dependencies=[Depends(RateLimiter(3, 60, "auth"))])
async def signup_route(payload: UserRegisterRequest, ctrl: AuthController = Depends(get_controller)):
    return await ctrl.handle_signup(payload)


@router.post("/verify-signup", response_model=TokenResponse, dependencies=[Depends(RateLimiter(3, 60, "auth"))])
async def verify_signup_route(
    payload: OTPVerificationRequest,
    response: Response,
    ctrl: AuthController = Depends(get_controller),
):
    data = await ctrl.handle_verify_signup(payload)
    return _issue_tokens_response(response, data)


@router.post("/resend-signup-otp", status_code=200, dependencies=[Depends(RateLimiter(3, 60, "auth"))])
async def resend_signup_otp_route(payload: ResendOtpRequest, ctrl: AuthController = Depends(get_controller)):
    return await ctrl.handle_resend_signup_otp(payload)


@router.post("/login", status_code=200, dependencies=[Depends(RateLimiter(3, 60, "auth"))])
async def login_route(
    payload: UserLoginRequest,
    response: Response,
    ctrl: AuthController = Depends(get_controller),
):
    result = await ctrl.handle_login(payload)
    return _issue_tokens_response(response, result)


@router.post("/verify-login", response_model=TokenResponse, dependencies=[Depends(RateLimiter(3, 60, "auth"))])
async def verify_login_route(
    payload: OTPVerificationRequest,
    response: Response,
    ctrl: AuthController = Depends(get_controller),
):
    data = await ctrl.handle_verify_login(payload)
    return _issue_tokens_response(response, data)


@router.post("/resend-login-otp", status_code=200, dependencies=[Depends(RateLimiter(3, 60, "auth"))])
async def resend_login_otp_route(payload: ResendOtpRequest, ctrl: AuthController = Depends(get_controller)):
    return await ctrl.handle_resend_login_otp(payload)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_route(
    request: Request,
    response: Response,
    payload: TokenRefreshRequest | None = None,
    ctrl: AuthController = Depends(get_controller),
):
    refresh_token = None
    if payload and payload.refresh_token:
        refresh_token = payload.refresh_token
    else:
        refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        from fastapi import HTTPException, status as http_status
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided.",
        )

    data = await ctrl.handle_refresh_raw(refresh_token)
    return _issue_tokens_response(response, data)


@router.post("/logout", status_code=200)
async def logout_route(
    request: Request,
    response: Response,
    ctrl: AuthController = Depends(get_controller),
):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        await ctrl.handle_logout(refresh_token)
    delete_refresh_cookie(response, is_production=_IS_PROD)
    return {"message": "Logged out successfully."}


@router.post("/password-reset/initiate", status_code=200, dependencies=[Depends(RateLimiter(3, 60, "auth"))])
async def reset_initiate_route(payload: PasswordResetInitiate, ctrl: AuthController = Depends(get_controller)):
    return await ctrl.handle_password_reset_request(payload)


@router.post("/password-reset/confirm", status_code=200, dependencies=[Depends(RateLimiter(3, 60, "auth"))])
async def reset_confirm_route(payload: PasswordResetConfirm, ctrl: AuthController = Depends(get_controller)):
    return await ctrl.handle_password_reset_confirm(payload)

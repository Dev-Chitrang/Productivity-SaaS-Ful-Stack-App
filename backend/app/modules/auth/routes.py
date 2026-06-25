from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.core.database import get_db
from app.core.redis import get_redis_client
from app.modules.auth.repository import AuthRepository
from app.modules.auth.service import AuthService
from app.modules.auth.controller import AuthController
from app.modules.auth.schema import (
    UserRegisterRequest, OTPVerificationRequest, UserLoginRequest,
    TokenRefreshRequest, PasswordResetInitiate, PasswordResetConfirm,
    ResendOtpRequest, TokenResponse, GoogleOAuthRequest, GoogleOAuthResponse
)

router = APIRouter(prefix="/auth", tags=["Identity Operations Infrastructure"])

async def get_controller(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis_client)
) -> AuthController:
    repo = AuthRepository(db)
    service = AuthService(repo, redis)
    return AuthController(service)

@router.post("/google", response_model=GoogleOAuthResponse, status_code=200)
async def google_oauth_route(payload: GoogleOAuthRequest, ctrl: AuthController = Depends(get_controller)):
    """
    Accepts a Google ID Token from the frontend OAuth popup.
    Verifies it server-side and either creates a new account or logs in
    an existing one.  Returns JWT tokens, or a 2FA challenge if enabled.
    """
    return await ctrl.handle_google_oauth(payload)

@router.post("/signup", status_code=201)
async def signup_route(payload: UserRegisterRequest, ctrl: AuthController = Depends(get_controller)):
    return await ctrl.handle_signup(payload)

@router.post("/verify-signup", response_model=TokenResponse)
async def verify_signup_route(payload: OTPVerificationRequest, ctrl: AuthController = Depends(get_controller)):
    return await ctrl.handle_verify_signup(payload)

@router.post("/resend-signup-otp", status_code=200)
async def resend_signup_otp_route(payload: ResendOtpRequest, ctrl: AuthController = Depends(get_controller)):
    return await ctrl.handle_resend_signup_otp(payload)

@router.post("/login", status_code=200)
async def login_route(payload: UserLoginRequest, ctrl: AuthController = Depends(get_controller)):
    return await ctrl.handle_login(payload)

@router.post("/verify-login", response_model=TokenResponse)
async def verify_login_route(payload: OTPVerificationRequest, ctrl: AuthController = Depends(get_controller)):
    return await ctrl.handle_verify_login(payload)

@router.post("/resend-login-otp", status_code=200)
async def resend_login_otp_route(payload: ResendOtpRequest, ctrl: AuthController = Depends(get_controller)):
    return await ctrl.handle_resend_login_otp(payload)

@router.post("/refresh", response_model=TokenResponse)
async def refresh_route(payload: TokenRefreshRequest, ctrl: AuthController = Depends(get_controller)):
    return await ctrl.handle_refresh(payload)

@router.post("/password-reset/initiate", status_code=200)
async def reset_initiate_route(payload: PasswordResetInitiate, ctrl: AuthController = Depends(get_controller)):
    return await ctrl.handle_password_reset_request(payload)

@router.post("/password-reset/confirm", status_code=200)
async def reset_confirm_route(payload: PasswordResetConfirm, ctrl: AuthController = Depends(get_controller)):
    return await ctrl.handle_password_reset_confirm(payload)

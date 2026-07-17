from starlette.responses import Response

REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_TOKEN_TTL = 604800  # 7 days in seconds


def set_refresh_cookie(response: Response, token: str, *, is_production: bool = False) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        max_age=REFRESH_TOKEN_TTL,
        httponly=True,
        secure=is_production,
        samesite="lax",
        path="/",
    )


def delete_refresh_cookie(response: Response, *, is_production: bool = False) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        httponly=True,
        secure=is_production,
        samesite="lax",
        path="/",
    )

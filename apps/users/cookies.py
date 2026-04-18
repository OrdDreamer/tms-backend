from django.conf import settings


def set_refresh_cookie(response, refresh_token: str) -> None:
    cfg = settings.JWT_COOKIE
    max_age = int(
        settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()
    )
    response.set_cookie(
        key=cfg["REFRESH_COOKIE_NAME"],
        value=refresh_token,
        max_age=max_age,
        path=cfg["COOKIE_PATH"],
        domain=cfg["COOKIE_DOMAIN"],
        secure=cfg["COOKIE_SECURE"],
        httponly=cfg["COOKIE_HTTPONLY"],
        samesite=cfg["COOKIE_SAMESITE"],
    )


def delete_refresh_cookie(response) -> None:
    cfg = settings.JWT_COOKIE
    response.delete_cookie(
        key=cfg["REFRESH_COOKIE_NAME"],
        path=cfg["COOKIE_PATH"],
        domain=cfg["COOKIE_DOMAIN"],
        samesite=cfg["COOKIE_SAMESITE"],
    )


def get_refresh_token_from_cookie(request) -> str | None:
    return request.COOKIES.get(settings.JWT_COOKIE["REFRESH_COOKIE_NAME"])

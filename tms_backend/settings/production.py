from .base import *  # noqa: F403
from .base import MIDDLEWARE as BASE_MIDDLEWARE
from .base import env

DEBUG = False

_middleware = list(BASE_MIDDLEWARE)
_security_at = _middleware.index(
    "django.middleware.security.SecurityMiddleware",
)
_middleware.insert(
    _security_at + 1,
    "whitenoise.middleware.WhiteNoiseMiddleware",
)
MIDDLEWARE = _middleware

DATABASES = {
    "default": env.db("DATABASE_URL"),
}

# Security settings
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

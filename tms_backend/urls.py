from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from apps.core.throttling import LoginRateThrottle
from apps.core.views import LanguageListAPIView
from apps.translations.views import PublicProjectTranslationsAPIView
from apps.users.views import (
    CookieTokenObtainPairView,
    CookieTokenRefreshView,
    UserLogoutAPIView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api-auth/", include("rest_framework.urls")),
    path(
        "api/v1/auth/token/",
        CookieTokenObtainPairView.as_view(
            throttle_classes=[LoginRateThrottle]
        ),
        name="token-obtain-pair",
    ),
    path(
        "api/v1/auth/token/refresh/",
        CookieTokenRefreshView.as_view(),
        name="token-refresh",
    ),
    path(
        "api/v1/auth/logout/", UserLogoutAPIView.as_view(), name="auth-logout"
    ),
    path("api/", include("apps.core.urls")),
    path(
        "api/v1/languages/",
        LanguageListAPIView.as_view(),
        name="language-list",
    ),
    path("api/v1/projects/", include("apps.projects.urls")),
    path("api/v1/users/", include("apps.users.urls")),
    path(
        "api/v1/public/<slug:project_slug>/translations/",
        PublicProjectTranslationsAPIView.as_view(),
        name="public-translations",
    ),
]

if settings.DEBUG:
    from drf_spectacular.views import (
        SpectacularAPIView,
        SpectacularRedocView,
        SpectacularSwaggerView,
    )

    urlpatterns += [
        path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
        path(
            "api/docs/",
            SpectacularSwaggerView.as_view(url_name="schema"),
            name="swagger-ui",
        ),
        path(
            "api/schema/redoc/",
            SpectacularRedocView.as_view(url_name="schema"),
            name="redoc",
        ),
    ]

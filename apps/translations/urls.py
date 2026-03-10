from django.urls import path

from apps.translations.views import (
    TranslationDetailAPIView,
    TranslationKeyBulkDeleteAPIView,
    TranslationKeyDetailAPIView,
    TranslationKeyListCreateAPIView,
    TranslationListAPIView,
)

app_name = "translations"

urlpatterns = [
    path(
        "",
        TranslationKeyListCreateAPIView.as_view(),
        name="translation-key-list",
    ),
    path(
        "bulk-delete/",
        TranslationKeyBulkDeleteAPIView.as_view(),
        name="translation-key-bulk-delete",
    ),
    path(
        "<str:key_name>/",
        TranslationKeyDetailAPIView.as_view(),
        name="translation-key-detail",
    ),
    path(
        "<str:key_name>/translations/",
        TranslationListAPIView.as_view(),
        name="translation-list",
    ),
    path(
        "<str:key_name>/translations/<str:lang_code>/",
        TranslationDetailAPIView.as_view(),
        name="translation-detail",
    ),
]

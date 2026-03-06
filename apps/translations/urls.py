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
        "<uuid:key_id>/",
        TranslationKeyDetailAPIView.as_view(),
        name="translation-key-detail",
    ),
    path(
        "<uuid:key_id>/translations/",
        TranslationListAPIView.as_view(),
        name="translation-list",
    ),
    path(
        "<uuid:key_id>/translations/<str:lang_code>/",
        TranslationDetailAPIView.as_view(),
        name="translation-detail",
    ),
]

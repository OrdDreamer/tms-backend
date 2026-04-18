from django.urls import path

from apps.users.views import (
    UserChangePasswordAPIView,
    UserDetailAPIView,
    UserListAPIView,
    UserMeAPIView,
)

app_name = "users"

urlpatterns = [
    path("", UserListAPIView.as_view(), name="user-list"),
    path("<int:user_id>/", UserDetailAPIView.as_view(), name="user-detail"),
    path("me/", UserMeAPIView.as_view(), name="user-me"),
    path(
        "me/change-password/",
        UserChangePasswordAPIView.as_view(),
        name="user-change-password",
    ),
]

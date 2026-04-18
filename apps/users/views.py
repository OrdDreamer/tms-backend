from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.core.exceptions import AuthError
from apps.users.cookies import (
    delete_refresh_cookie,
    get_refresh_token_from_cookie,
    set_refresh_cookie,
)
from apps.users.models import User
from apps.users.serializers import (
    CookieTokenObtainOutputSerializer,
    CookieTokenRefreshOutputSerializer,
    UserChangePasswordInputSerializer,
    UserChangePasswordOutputSerializer,
    UserDetailOutputSerializer,
    UserListFilterSerializer,
    UserListOutputSerializer,
    UserMeUpdateInputSerializer,
)
from apps.users.utils import user_change_password, user_logout, user_update


class CookieTokenObtainPairView(TokenObtainPairView):
    @extend_schema(
        summary="Obtain JWT pair (login)",
        responses={200: CookieTokenObtainOutputSerializer},
        tags=["Auth"],
    )
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            refresh_token = response.data.pop("refresh")
            set_refresh_cookie(response, refresh_token)
        return response


class CookieTokenRefreshView(APIView):
    permission_classes = ()
    authentication_classes = ()

    @extend_schema(
        summary="Refresh access token",
        request=None,
        responses={200: CookieTokenRefreshOutputSerializer},
        tags=["Auth"],
    )
    def post(self, request):
        refresh_token = get_refresh_token_from_cookie(request)
        if not refresh_token:
            return Response(
                {"message": "Refresh token cookie missing.", "extra": {}},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        serializer = TokenRefreshSerializer(data={"refresh": refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError:
            return Response(
                {"message": "Token is invalid or expired.", "extra": {}},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        response = Response(
            {"access": str(serializer.validated_data["access"])}
        )
        new_refresh = serializer.validated_data.get("refresh")
        if new_refresh:
            set_refresh_cookie(response, str(new_refresh))
        return response


class UserLogoutAPIView(APIView):
    permission_classes = ()

    @extend_schema(
        summary="Logout (blacklist refresh token)",
        request=None,
        responses={204: None},
        tags=["Auth"],
    )
    def post(self, request):
        refresh_token = get_refresh_token_from_cookie(request)
        if refresh_token:
            try:
                user_logout(refresh_token=refresh_token)
            except AuthError:
                pass
        response = Response(status=status.HTTP_204_NO_CONTENT)
        delete_refresh_cookie(response)
        return response


class UserListAPIView(APIView):
    class Pagination(LimitOffsetPagination):
        default_limit = 20
        max_limit = 100

    pagination_class = Pagination

    @extend_schema(
        summary="List users",
        parameters=[
            OpenApiParameter(
                name="search",
                description="Filter by email, first name or last name",
                required=False,
                type=str,
            )
        ],
        responses=UserListOutputSerializer(many=True),
        tags=["Users"],
    )
    def get(self, request):
        filters = UserListFilterSerializer(data=request.query_params)
        filters.is_valid(raise_exception=True)

        qs = User.objects.all().order_by("email")

        search = filters.validated_data.get("search")
        if search:
            qs = qs.filter(
                Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
            )

        paginator = self.Pagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = UserListOutputSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class UserDetailAPIView(APIView):
    @extend_schema(
        summary="Retrieve user details",
        responses=UserDetailOutputSerializer,
        tags=["Users"],
    )
    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        serializer = UserDetailOutputSerializer(user)
        return Response(serializer.data)


class UserChangePasswordAPIView(APIView):
    @extend_schema(
        summary="Change current user password",
        request=UserChangePasswordInputSerializer,
        responses=UserChangePasswordOutputSerializer,
        tags=["Users"],
    )
    def post(self, request):
        serializer = UserChangePasswordInputSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        user = user_change_password(
            user=request.user,
            current_password=serializer.validated_data["current_password"],
            new_password=serializer.validated_data["new_password"],
        )
        refresh = RefreshToken.for_user(user)
        response = Response({"access": str(refresh.access_token)})
        set_refresh_cookie(response, str(refresh))
        return response


class UserMeAPIView(APIView):
    @extend_schema(
        summary="Get current user profile",
        responses=UserDetailOutputSerializer,
        tags=["Users"],
    )
    def get(self, request):
        serializer = UserDetailOutputSerializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        summary="Update current user profile",
        request=UserMeUpdateInputSerializer,
        responses=UserDetailOutputSerializer,
        tags=["Users"],
    )
    def patch(self, request):
        serializer = UserMeUpdateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = user_update(
            user=request.user,
            first_name=serializer.validated_data.get("first_name"),
            last_name=serializer.validated_data.get("last_name"),
        )

        output = UserDetailOutputSerializer(user)
        return Response(output.data)

from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User
from apps.users.serializers import (
    UserChangePasswordInputSerializer,
    UserChangePasswordOutputSerializer,
    UserDetailOutputSerializer,
    UserListFilterSerializer,
    UserListOutputSerializer,
    UserLogoutInputSerializer,
    UserMeUpdateInputSerializer,
)
from apps.users.utils import user_change_password, user_logout, user_update


class UserLogoutAPIView(APIView):
    permission_classes = []

    @extend_schema(
        summary="Logout (blacklist refresh token)",
        request=UserLogoutInputSerializer,
        responses={204: None},
        tags=["Auth"],
    )
    def post(self, request):
        serializer = UserLogoutInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_logout(refresh_token=serializer.validated_data["refresh"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserListAPIView(APIView):
    class Pagination(LimitOffsetPagination):
        default_limit = 20
        max_limit = 100

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
            new_password=serializer.validated_data["new_password"],
        )
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })


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

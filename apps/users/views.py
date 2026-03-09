from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User
from apps.users.serializers import (
    UserChangePasswordInputSerializer,
    UserDetailOutputSerializer,
    UserListFilterSerializer,
    UserListOutputSerializer,
    UserMeUpdateInputSerializer,
)
from apps.users.utils import user_change_password, user_update


class UserListAPIView(APIView):
    """
    GET — list users (read-only, paginated).
    """

    class Pagination(LimitOffsetPagination):
        default_limit = 20
        max_limit = 100

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
    """
    GET — retrieve user details by id.
    """

    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        serializer = UserDetailOutputSerializer(user)
        return Response(serializer.data)


class UserChangePasswordAPIView(APIView):
    """
    POST — change current user password and return new access/refresh tokens.
    """

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
    """
    GET   — get current user profile.
    PATCH — update current user profile.
    """

    def get(self, request):
        serializer = UserDetailOutputSerializer(request.user)
        return Response(serializer.data)

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

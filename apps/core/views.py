from django.db import OperationalError, connection
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.choices import LanguageChoices
from apps.core.serializers import (
    HealthCheckOutputSerializer,
    LanguageOutputSerializer,
)


class HealthCheckAPIView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)
    throttle_classes = ()

    @extend_schema(
        summary="Health check",
        responses={
            200: HealthCheckOutputSerializer,
            503: HealthCheckOutputSerializer,
        },
        tags=["Infrastructure"],
    )
    def get(self, request):
        db_status = "ok"
        http_status = status.HTTP_200_OK

        try:
            connection.ensure_connection()
        except OperationalError:
            db_status = "unavailable"
            http_status = status.HTTP_503_SERVICE_UNAVAILABLE

        output = HealthCheckOutputSerializer(
            {
                "status": "ok" if http_status == 200 else "error",
                "db": db_status,
            }
        )
        return Response(output.data, status=http_status)


class LanguageListAPIView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)
    throttle_classes = ()

    @extend_schema(
        summary="List available languages",
        responses=LanguageOutputSerializer(many=True),
        tags=["Languages"],
    )
    def get(self, request):
        data = [
            {"code": code, "name": name}
            for code, name in LanguageChoices.choices
        ]
        serializer = LanguageOutputSerializer(data, many=True)
        return Response(serializer.data)

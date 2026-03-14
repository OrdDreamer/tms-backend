from django.db import connection, OperationalError
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.serializers import HealthCheckOutputSerializer


class HealthCheckAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = []

    @extend_schema(
        summary="Health check",
        responses={200: HealthCheckOutputSerializer, 503: HealthCheckOutputSerializer},
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

        output = HealthCheckOutputSerializer({
            "status": "ok" if http_status == 200 else "error",
            "db": db_status,
        })
        return Response(output.data, status=http_status)

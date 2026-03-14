from rest_framework import serializers


class HealthCheckOutputSerializer(serializers.Serializer):
    status = serializers.CharField()
    db = serializers.CharField()

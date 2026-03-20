from rest_framework import serializers


class HealthCheckOutputSerializer(serializers.Serializer):
    status = serializers.CharField()
    db = serializers.CharField()


class LanguageOutputSerializer(serializers.Serializer):
    code = serializers.CharField()
    name = serializers.CharField()

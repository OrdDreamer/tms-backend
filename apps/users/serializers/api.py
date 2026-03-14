from rest_framework import serializers

# ----------------------
# User
# ----------------------


class UserListFilterSerializer(serializers.Serializer):
    search = serializers.CharField(required=False)


class UserListOutputSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    date_joined = serializers.DateTimeField()


class UserDetailOutputSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    date_joined = serializers.DateTimeField()
    last_login = serializers.DateTimeField(allow_null=True)


class UserMeUpdateInputSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)


class UserLogoutInputSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class UserChangePasswordOutputSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


class UserChangePasswordInputSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "Passwords do not match."}
            )
        return attrs

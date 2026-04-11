from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for new user registration with password confirmation."""

    password = serializers.CharField(write_only=True, min_length=8)
    repeated_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'password', 'repeated_password')

    def validate(self, data):
        """Ensure both passwords match before creating the user."""
        if data['password'] != data['repeated_password']:
            raise serializers.ValidationError('Passwords do not match.')
        return data

    def create(self, validated_data):
        """Remove repeated_password and create the user."""
        validated_data.pop('repeated_password')
        return User.objects.create_user(**validated_data)


class PasswordResetSerializer(serializers.Serializer):
    """Serializer for requesting a password reset email."""

    email = serializers.EmailField()


class SetNewPasswordSerializer(serializers.Serializer):
    """Serializer for setting a new password after reset confirmation."""

    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        """Ensure both passwords match before resetting."""
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError('Passwords do not match.')
        return data
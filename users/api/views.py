from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from .serializers import RegisterSerializer, PasswordResetSerializer, SetNewPasswordSerializer
from users.utils import send_confirmation_email, send_password_reset_email, set_auth_cookies

User = get_user_model()


class RegisterView(APIView):
    """Handle new user registration."""

    def post(self, request):
        """Create a new inactive user and send a confirmation email."""
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'detail': 'Please check your input.'}, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.save()
        send_confirmation_email(user)
        return Response({'detail': 'Registration successful. Please confirm your email.'}, status=status.HTTP_201_CREATED)


class ActivateAccountView(APIView):
    """Handle account activation via email link."""

    def post(self, request):
        """Activate user account using uid and token from the confirmation email."""
        uid = request.data.get('uid')
        token = request.data.get('token')
        user = get_user_from_uid(uid)
        if not user:
            return Response({'detail': 'Invalid activation link.'}, status=status.HTTP_400_BAD_REQUEST)
        if not default_token_generator.check_token(user, token):
            return Response({'detail': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)
        user.is_active = True
        user.save()
        return Response({'detail': 'Account activated successfully.'}, status=status.HTTP_200_OK)


class LoginView(APIView):
    """Handle user login and JWT cookie assignment."""

    def post(self, request):
        """Authenticate user and set JWT tokens as HttpOnly cookies."""
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(request, username=email, password=password)
        if not user:
            return Response({'detail': 'Please check your input.'}, status=status.HTTP_401_UNAUTHORIZED)
        tokens = RefreshToken.for_user(user)
        response = Response({'detail': 'Login successful.'}, status=status.HTTP_200_OK)
        return set_auth_cookies(response, tokens)


class LogoutView(APIView):
    """Handle user logout and token blacklisting."""

    def post(self, request):
        """Blacklist the refresh token and delete auth cookies."""
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response({'detail': 'Refresh token missing.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response({'detail': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)
        response = Response({'detail': 'Logout successful! All tokens will be deleted. Refresh token is now invalid.'}, status=status.HTTP_200_OK)
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response


class PasswordResetRequestView(APIView):
    """Handle password reset email requests."""

    def post(self, request):
        """Send a password reset email if the provided email exists."""
        serializer = PasswordResetSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'detail': 'Please check your input.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(email=serializer.validated_data['email'])
            send_password_reset_email(user)
        except User.DoesNotExist:
            pass
        return Response({'detail': 'An email has been sent to reset your password.'}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """Handle password reset confirmation via uid and token."""

    def post(self, request, uidb64, token):
        """Validate token and set new password for the user."""
        serializer = SetNewPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'detail': 'Please check your input.'}, status=status.HTTP_400_BAD_REQUEST)
        user = get_user_from_uid(uidb64)
        if not user:
            return Response({'detail': 'Invalid link.'}, status=status.HTTP_400_BAD_REQUEST)
        if not default_token_generator.check_token(user, token):
            return Response({'detail': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'detail': 'Your Password has been successfully reset.'}, status=status.HTTP_200_OK)


def get_user_from_uid(uid):
    """Decode a base64 uid and return the corresponding user or None."""
    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        return User.objects.get(pk=user_id)
    except (User.DoesNotExist, ValueError):
        return None
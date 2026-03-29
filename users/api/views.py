from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from .serializers import RegisterSerializer, PasswordResetSerializer, SetNewPasswordSerializer
from users.utils import send_confirmation_email, send_password_reset_email

User = get_user_model()


class RegisterView(APIView):

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'detail': 'Please check your input.'}, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.save()
        send_confirmation_email(user)
        return Response({'detail': 'Registration successful. Please confirm your email.'}, status=status.HTTP_201_CREATED)


class ActivateAccountView(APIView):

    def post(self, request):
        uid = request.data.get('uid')
        token = request.data.get('token')
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, ValueError):
            return Response({'detail': 'Invalid activation link.'}, status=status.HTTP_400_BAD_REQUEST)
        if not default_token_generator.check_token(user, token):
            return Response({'detail': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)
        user.is_active = True
        user.save()
        return Response({'detail': 'Account activated successfully.'}, status=status.HTTP_200_OK)


class LoginView(APIView):

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(request, username=email, password=password)
        if not user:
            return Response({'detail': 'Please check your input.'}, status=status.HTTP_401_UNAUTHORIZED)
        tokens = RefreshToken.for_user(user)
        response = Response({'detail': 'Login successful.'}, status=status.HTTP_200_OK)
        response = set_auth_cookies(response, tokens)
        return response


class LogoutView(APIView):

    def post(self, request):
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

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'detail': 'Please check your input.'}, status=status.HTTP_400_BAD_REQUEST)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            send_password_reset_email(user)
        except User.DoesNotExist:
            pass
        return Response({'detail': 'An email has been sent to reset your password.'}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):

    def post(self, request, uidb64, token):
        serializer = SetNewPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'detail': 'Please check your input.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, ValueError):
            return Response({'detail': 'Invalid link.'}, status=status.HTTP_400_BAD_REQUEST)
        if not default_token_generator.check_token(user, token):
            return Response({'detail': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'detail': 'Your Password has been successfully reset.'}, status=status.HTTP_200_OK)


def set_auth_cookies(response, tokens):
    response.set_cookie(
        key='access_token',
        value=str(tokens.access_token),
        httponly=True,
        samesite='Lax',
        secure=False,
    )
    response.set_cookie(
        key='refresh_token',
        value=str(tokens),
        httponly=True,
        samesite='Lax',
        secure=False,
    )
    return response
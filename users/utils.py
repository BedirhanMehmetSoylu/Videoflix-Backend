from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


class CookieJWTAuthentication(JWTAuthentication):
    """Authenticates users via JWT token stored in HttpOnly cookie."""

    def authenticate(self, request):
        """Extract and validate JWT token from cookie."""
        access_token = request.COOKIES.get('access_token')
        if not access_token:
            return None
        try:
            validated_token = self.get_validated_token(access_token)
            return self.get_user(validated_token), validated_token
        except InvalidToken:
            return None


def send_confirmation_email(user):
    """Send account activation email with a unique confirmation link."""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    link = f"{settings.FRONTEND_URL}/pages/auth/activate.html?uid={uid}&token={token}"
    send_mail(
        subject='Confirm your Videoflix account',
        message=f'Please click the link to activate your account: {link}',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )


def send_password_reset_email(user):
    """Send password reset email with a unique reset link."""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    link = f"{settings.FRONTEND_URL}/pages/auth/reset-password.html?uid={uid}&token={token}"
    send_mail(
        subject='Reset your Videoflix password',
        message=f'Please click the link to reset your password: {link}',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )


def set_auth_cookies(response, tokens):
    """Set JWT access and refresh tokens as HttpOnly cookies on the response."""
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
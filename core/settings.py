"""
Django settings for core project.
"""

from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', default='django-insecure-@#x5h3zj!g+8g1v@2^b6^9$8&f1r7g$@t3v!p4#=g0r5qzj4m3')

DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", default="localhost").split(",")
CSRF_TRUSTED_ORIGINS = os.environ.get("CSRF_TRUSTED_ORIGINS", default="http://localhost:4200").split(",")

AUTH_USER_MODEL = 'users.CustomUser'

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'users.utils.CookieJWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
}

CORS_ALLOW_CREDENTIALS = True
# Only our own frontend domains may call the API, instead of
# hardcoded localhost-only origins.
CORS_ALLOWED_ORIGINS = os.environ.get(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:5500,http://127.0.0.1:5500'
).split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'users',
    'videos',
]

# django_rq (and the underlying rq library) tries to use
# multiprocessing.get_context('fork') on import, which does not exist on
# Windows. Only load it when REDIS_URL is actually configured (i.e. in
# production on Render/Linux), so local Windows development without Redis
# doesn't crash on every manage.py command.
if os.environ.get('REDIS_URL'):
    INSTALLED_APPS += ['django_rq']

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'users' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# ========================
# DATABASE
# ========================
#
# Uses DATABASE_URL from the environment (e.g. the Neon Postgres connection
# string). Falls back to SQLite locally if not set.

DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=True)
    }
    # Neon (our Postgres provider) proactively closes idle connections to
    # save resources. Our background RQ worker keeps a DB connection open
    # for up to conn_max_age (600s) between jobs; if Neon closes it in the
    # meantime, Django would otherwise try to reuse the now-dead connection
    # and crash with "SSL connection has been closed unexpectedly".
    # CONN_HEALTH_CHECKS makes Django ping the connection before reuse and
    # transparently reconnect if it's stale, instead of erroring out.
    DATABASES['default']['CONN_HEALTH_CHECKS'] = True
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ========================
# REDIS (cache + RQ task queue)
# ========================
#
# Uses REDIS_URL from the environment (e.g. an Upstash "rediss://..." URL).
# Falls back to local in-memory cache and a local Redis instance for RQ.

REDIS_URL = os.environ.get('REDIS_URL')

if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient"
            },
            "KEY_PREFIX": "videoflix"
        }
    }
    RQ_QUEUES = {
        'default': {
            'URL': REDIS_URL,
            'DEFAULT_TIMEOUT': 900,
        },
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
    RQ_QUEUES = {
        'default': {
            'HOST': os.environ.get("REDIS_HOST", "localhost"),
            'PORT': os.environ.get("REDIS_PORT", 6379),
            'DB': os.environ.get("REDIS_DB", 0),
            'DEFAULT_TIMEOUT': 900,
        },
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"

MEDIA_URL = "/media/"
# On Render, this is set to the mount path of a Persistent Disk (e.g.
# /var/data), so uploaded videos and processed HLS files survive deploys
# and restarts. Render's default local disk is ephemeral and gets wiped on
# every deploy. Locally, this falls back to a regular folder in the project.
MEDIA_ROOT = Path(os.environ.get('MEDIA_ROOT', BASE_DIR / "media"))

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@videoflix.com')

FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://127.0.0.1:5500')

# When DEBUG=False (i.e. in production), enable additional security headers
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
"""
Django settings for amoneyplan project.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
SECRET_KEY = "django-insecure-change-this-in-production"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]  # Allow all hosts in development

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    # Third party apps
    "corsheaders",
    "strawberry.django",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    # Local apps
    "amoneyplan.accounts",
    "amoneyplan.money_plans",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "amoneyplan.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "amoneyplan.wsgi.application"

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "amoneyplan"),
        "USER": os.environ.get("DB_USER", "postgres"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "postgres"),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}

# Logging configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": True,
        },
        "amoneyplan": {
            "handlers": ["console"],
            "level": os.getenv("MP_LOG_LEVEL", "INFO"),
            "propagate": True,
        },
    },
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# CORS settings
CORS_ALLOW_ALL_ORIGINS = DEBUG  # In development allow all origins
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:8000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
]

FRONTEND_URL = "http://localhost:5173"  # Development frontend URL

# Session settings
SESSION_COOKIE_SAMESITE = "Lax" if DEBUG else "Strict"
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True

# CSRF settings
CSRF_TRUSTED_ORIGINS = ["http://localhost:8000", "http://127.0.0.1:8000"]
CSRF_COOKIE_SECURE = not DEBUG
CSRF_USE_SESSIONS = False
CSRF_COOKIE_HTTPONLY = False  # Allow JavaScript access to CSRF token
CSRF_COOKIE_SAMESITE = "Lax" if DEBUG else "Strict"

# Custom user model
AUTH_USER_MODEL = "accounts.User"

# Authentication settings
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# django-allauth settings
SITE_ID = 1
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "none"  # TODO Change to "mandatory" in production
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": os.environ.get("GOOGLE_CLIENT_ID", ""),
            "secret": os.environ.get("GOOGLE_CLIENT_SECRET", ""),
            "key": "",
        },
        "SCOPE": [
            "profile",
            "email",
        ],
    }
}

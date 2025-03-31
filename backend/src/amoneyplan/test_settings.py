"""
Django test settings for amoneyplan project.
"""

from .settings import *  # noqa

# Override database settings for testing to use SQLite in memory
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Speed up password hashing in tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable logging during tests
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["null"],
            "level": "ERROR",
            "propagate": False,
        },
        "amoneyplan": {
            "handlers": ["null"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}

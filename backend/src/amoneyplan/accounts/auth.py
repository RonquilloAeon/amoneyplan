from datetime import timedelta
from typing import TYPE_CHECKING

import jwt
from django.conf import settings

from amoneyplan.common.time import get_utc_now

if TYPE_CHECKING:
    from .models import User


def generate_token(user: "User") -> str:
    payload = {
        "user_id": str(user.id),
        "exp": get_utc_now() + timedelta(seconds=settings.JWT_EXPIRATION_SECONDS),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token

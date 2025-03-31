# middleware.py

import logging

import jwt
from django.conf import settings

from amoneyplan.accounts.models import User
from amoneyplan.accounts.tenancy import set_current_account

logger = logging.getLogger(__name__)


class JWTAuthenticationMiddleware:
    """
    Middleware to authenticate users using JWT tokens.
    """

    def __init__(self, get_response):
        self.get_response = get_response  # Required by Django middleware

    def __call__(self, request):
        auth_header = request.headers.get("Authorization", None)

        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

                user = User.objects.get(id=payload["user_id"])
                request.user = user

                # Set current account (simplified for now)
                user_accounts = user.accounts.all()
                if user_accounts.exists():
                    logger.info("Setting current account for user '%s': '%s'", user, user_accounts.first())
                    set_current_account(user_accounts.first())
            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, User.DoesNotExist) as e:
                logger.error(f"JWT Authentication failed: {str(e)}")
                request.user = None

        response = self.get_response(request)
        return response

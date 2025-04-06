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
        logger.info(f"Auth header: {auth_header}")
        logger.info(f"All request headers: {request.headers}")

        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                logger.info(f"Processing token: {token[:10]}...")
                logger.info(f"Using SECRET_KEY: {settings.SECRET_KEY[:10]}...")
                logger.info(f"Using JWT_ALGORITHM: {settings.JWT_ALGORITHM}")

                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
                logger.info(f"Token payload: {payload}")

                user = User.objects.get(id=payload["user_id"])
                logger.info(f"Found user: {user.username}")
                request.user = user
                logger.info(f"Set request.user to: {request.user}")

                # Set current account (simplified for now)
                user_accounts = user.accounts.all()
                if user_accounts.exists():
                    logger.info("Setting current account for user '%s': '%s'", user, user_accounts.first())
                    set_current_account(user_accounts.first())
            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, User.DoesNotExist) as e:
                logger.error(f"JWT Authentication failed: {str(e)}")
                request.user = None
        else:
            logger.info("No valid Authorization header found")

        response = self.get_response(request)
        return response

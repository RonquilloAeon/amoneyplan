import strawberry
from allauth.socialaccount.helpers import complete_social_login
from allauth.socialaccount.models import SocialApp
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from strawberry.types import Info

from amoneyplan.users.models import User


@strawberry.type
class UserType:
    id: strawberry.ID
    username: str
    email: str
    first_name: str
    last_name: str


@strawberry.type
class AuthError:
    message: str


@strawberry.type
class GoogleAuthResponse:
    auth_url: str


@strawberry.type
class AuthResponse:
    success: bool
    user: UserType | None = None
    error: AuthError | None = None


@strawberry.type
class AuthMutations:
    @strawberry.mutation
    def google_auth_url(self, info: Info) -> GoogleAuthResponse:
        """Get the Google OAuth URL for initiating the login flow."""
        try:
            google_app = SocialApp.objects.get(provider="google")
            adapter = GoogleOAuth2Adapter(info.context.request)
            callback_url = f"{settings.FRONTEND_URL}/auth/google/callback"
            client = OAuth2Client(
                client_id=google_app.client_id,
                callback_url=callback_url,
            )
            auth_url, _ = adapter.get_auth_url(client, info.context.request)
            return GoogleAuthResponse(auth_url=auth_url)
        except Exception:
            return GoogleAuthResponse(auth_url="")

    @strawberry.mutation
    def register(
        self,
        info: Info,
        username: str,
        email: str,
        password: str,
        first_name: str = "",
        last_name: str = "",
    ) -> AuthResponse:
        try:
            if User.objects.filter(username=username).exists():
                return AuthResponse(success=False, error=AuthError(message="Username already exists"))

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )

            login(info.context.request, user)
            return AuthResponse(success=True, user=user)
        except Exception as e:
            return AuthResponse(success=False, error=AuthError(message=str(e)))

    @strawberry.mutation
    def login(
        self,
        info: Info,
        username: str,
        password: str,
    ) -> AuthResponse:
        user = authenticate(username=username, password=password)
        if user is None:
            return AuthResponse(success=False, error=AuthError(message="Invalid credentials"))

        login(info.context.request, user)
        return AuthResponse(success=True, user=user)

    @strawberry.mutation
    def logout(self, info: Info) -> AuthResponse:
        if info.context.request.user.is_authenticated:
            logout(info.context.request)
            return AuthResponse(success=True)
        return AuthResponse(success=False, error=AuthError(message="Not logged in"))

    @strawberry.mutation
    def google_callback(self, info: Info, code: str) -> AuthResponse:
        """Process Google OAuth callback and authenticate the user."""
        request = info.context.request
        try:
            google_app = SocialApp.objects.get(provider="google")
            adapter = GoogleOAuth2Adapter(request)
            callback_url = f"{settings.FRONTEND_URL}/auth/google/callback"
            client = OAuth2Client(
                client_id=google_app.client_id,
                callback_url=callback_url,
            )

            # Complete the OAuth2 flow
            access_token = adapter.get_access_token_data(
                code,
                client=client,
            )

            # Get user info from Google and authenticate
            token = access_token["access_token"]
            response = adapter.complete_login(request, app=google_app, token=token)

            # Set provider for the login
            response.sociallogin.state = {
                "process": "login",
                "scope": "",
                "auth_params": "",
            }

            # Complete the social login process
            complete_social_login(request, response.sociallogin)

            # If user is now authenticated, return success
            if request.user.is_authenticated:
                return AuthResponse(success=True, user=request.user)
            else:
                return AuthResponse(success=False, error=AuthError(message="Google authentication failed"))

        except Exception as e:
            return AuthResponse(
                success=False, error=AuthError(message=f"Google authentication error: {str(e)}")
            )


@strawberry.type
class AuthQueries:
    @strawberry.field
    def me(self, info: Info) -> UserType | None:
        if info.context.request.user.is_authenticated:
            return info.context.request.user
        return None

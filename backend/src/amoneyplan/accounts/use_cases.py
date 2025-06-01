import logging
from dataclasses import dataclass

from amoneyplan.accounts.models import Account, AccountMembership, User
from amoneyplan.common.use_cases import UseCaseException, UseCaseResult

logger = logging.getLogger("django")


@dataclass
class RegisterAccountData:
    username: str
    email: str
    password: str
    first_name: str | None = None
    last_name: str | None = None


class AccountUseCases:
    def register_account(self, data: RegisterAccountData) -> UseCaseResult[tuple[User, Account]]:
        if User.objects.filter(username=data.username).exists():
            return UseCaseResult.failure(UseCaseException(f"Username {data.username} already exists"))

        if User.objects.filter(email=data.email).exists():
            return UseCaseResult.failure(UseCaseException(f"Email {data.email} already exists"))

        try:
            user = User.objects.create_user(
                username=data.username,
                email=data.email,
                password=data.password,
                first_name=data.first_name or "",
                last_name=data.last_name or "",
            )
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return UseCaseResult.failure(
                UseCaseException("An unexpected error occurred while creating your user.")
            )

        try:
            account = Account.objects.create(
                owner=user,
                name=f"{data.username} Money Planning",
            )
        except Exception as e:
            logger.error(f"Error creating account: {e}")
            return UseCaseResult.failure(
                UseCaseException("An unexpected error occurred while creating your account.")
            )

        try:
            AccountMembership.objects.create(
                account=account,
                user=user,
                role="manager",
                status="active",
            )
        except Exception as e:
            logger.error(f"Error creating account membership: {e}")
            return UseCaseResult.failure(
                UseCaseException("An unexpected error occurred while configuring your account.")
            )

        return UseCaseResult.success((user, account))

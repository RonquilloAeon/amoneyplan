import pytest

from ulid import ULID

from amoneyplan.domain import Id, IllegalStateError
from amoneyplan.domain.account import Account
from amoneyplan.domain.category import Category
from amoneyplan.domain.money import Money


def test_account_lifecycle():
    account = Account(Id(str(ULID())), "Bank of Abc")

    assert account.categories == []

    with pytest.raises(IllegalStateError):
        account.mark_as_disbursed()

    assert account.is_disbursed is False

    # Add categories
    rent = Category(name="Rent", amount=Money.parse(1400))
    utilities = Category(name="Utilities", amount=Money.parse(650))
    cell_bill = Category(name="Cell Bill", amount=Money.parse(150))

    account.add_category(rent)
    account.add_category(utilities)
    account.add_category(cell_bill)

    # Check funds
    assert account.allocated_funds == Money.parse(2200)

    # Add and remove a category
    ira = Category(name="IRA", amount=Money.parse(200))
    account.add_category(ira)

    assert account.allocated_funds == Money.parse(2400)

    account.remove_category(ira)

    assert account.allocated_funds == Money.parse(2200)

    # Mark as disbursed
    account.mark_as_disbursed()

    assert account.is_disbursed is True


# TODO need to verify that account cannot be marked as disbursed if no categories
# TODO do we need to handle disabling account edits if it is disbursed?

USERS: dict[str, dict] = {
    "u-001": {"user_id": "u-001", "username": "alice"},
    "u-002": {"user_id": "u-002", "username": "bob"},
}

ACCOUNTS: dict[str, dict] = {
    "acc-001": {
        "account_id": "acc-001",
        "owner_id": "u-001",
        "account_type": "current",
        "balance_pence": 125050,
        "currency": "GBP",
        "iban": "GB00TEST00000000000001",
    },
    "acc-002": {
        "account_id": "acc-002",
        "owner_id": "u-001",
        "account_type": "savings",
        "balance_pence": 980000,
        "currency": "GBP",
        "iban": "GB00TEST00000000000002",
    },
    "acc-003": {
        "account_id": "acc-003",
        "owner_id": "u-002",
        "account_type": "current",
        "balance_pence": 4210,
        "currency": "GBP",
        "iban": "GB00TEST00000000000003",
    },
    "acc-004": {
        "account_id": "acc-004",
        "owner_id": "u-002",
        "account_type": "savings",
        "balance_pence": 2500000,
        "currency": "GBP",
        "iban": "GB00TEST00000000000004",
    },
    "acc-005": {
        "account_id": "acc-005",
        "owner_id": "u-002",
        "account_type": "current",
        "balance_pence": 0,
        "currency": "EUR",
        "iban": "GB00TEST00000000000005",
    },
}


def get_account(account_id: str) -> dict | None:
    return ACCOUNTS.get(account_id)


def find_accounts(
    *,
    owner_id: str | None = None,
    account_type: str | None = None,
    min_balance_pence: int | None = None,
) -> list[dict]:
    results = []
    for account in ACCOUNTS.values():
        if owner_id is not None and account["owner_id"] != owner_id:
            continue
        if (account_type is not None
                and account["account_type"] != account_type):
            continue
        if (min_balance_pence is not None
                and account["balance_pence"] < min_balance_pence):
            continue
        results.append(account)
    return results


if __name__ == "__main__":
    print(get_account("acc-001"))
    print(get_account("acc-999"))
    print(find_accounts(owner_id="u-001"))
    print(find_accounts(account_type="savings"))
    print(find_accounts(min_balance_pence=100000))
    print(find_accounts(min_balance_pence=0))

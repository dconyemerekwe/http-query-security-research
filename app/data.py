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

def find_accounts_by_owner(*, owner_id: str | None = None, account_type: str | None = None) -> List[dict]:
    return None

if __name__ == "__main__":
    print(get_account("acc-001"))
    print(get_account("acc-999"))
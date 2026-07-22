from app.mock_db import MOCK_USERS_DB


def get_sample_customer_profile(account_number: str) -> dict:
    account = MOCK_USERS_DB.get(str(account_number).strip())
    if not account:
        return {"account_number": account_number, "status": "not_found"}

    return {
        "account_number": account_number,
        "name": account.get("name"),
        "account_type": account.get("account_type"),
        "balance": account.get("balance"),
        "loans": account.get("loans", []),
    }

from typing import Annotated

from fastapi import Depends, FastAPI, Query
from pydantic import BaseModel

from app import auth, data


class AccountFilter(BaseModel):  # BaseModel provides the data schema
    owner_id: str | None = None
    account_type: str | None = None
    min_balance_pence: int | None = None


# Annotated[Type, metadata]
CurrentUser = Annotated[str, Depends(auth.get_current_user)]

app = FastAPI()


def search_owned_accounts(f: AccountFilter, user_id: str) -> list[dict]:
    if f.owner_id is not None and f.owner_id != user_id:
        return []

    return data.find_accounts(
        owner_id=user_id,
        account_type=f.account_type,
        min_balance_pence=f.min_balance_pence,
    )


@app.get("/health")
def show_health():
    return {"status": "ok"}


@app.api_route("/accounts", methods=["QUERY"])
def query_accounts(f: AccountFilter, current_user: CurrentUser):
    return search_owned_accounts(f, current_user)


@app.get("/accounts")
def get_accounts(
    f: Annotated[AccountFilter, Query()],
    current_user: CurrentUser,
):
    return search_owned_accounts(f, current_user)


@app.post("/accounts/search")
def post_accounts(f: AccountFilter, current_user: CurrentUser):
    return search_owned_accounts(f, current_user)

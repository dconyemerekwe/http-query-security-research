from fastapi import FastAPI, Query, Depends, Header
from pydantic import BaseModel
from typing import Annotated
from app import data, auth

class AccountFilter(BaseModel): # inherits BaseModel for data schema definition
    owner_id: str | None = None
    account_type: str | None = None
    min_balance_pence: int | None = None

app = FastAPI()

def token(token: Annotated[str | None, Header()] = None):
    return auth.get_current_user(token)

@app.get("/health")
def show_health():
    return {"status": "ok"}

@app.api_route("/accounts", methods=["QUERY"])
def query_accounts(f: Annotated[AccountFilter, Query(), Depends(token)]):
    return data.find_accounts(owner_id=f.owner_id, account_type=f.account_type, min_balance_pence=f.min_balance_pence)

@app.get("/accounts")
def get_accounts(f: Annotated[AccountFilter, Query(), Depends(token)]): # Annotated[Type, metadata -> coming from: URL's query string]
    return data.find_accounts(owner_id=f.owner_id, account_type=f.account_type, min_balance_pence=f.min_balance_pence)

@app.post("/accounts/search")
def post_accounts(f: Annotated[AccountFilter, Query(), Depends(token)]):
    return data.find_accounts(owner_id=f.owner_id, account_type=f.account_type, min_balance_pence=f.min_balance_pence)
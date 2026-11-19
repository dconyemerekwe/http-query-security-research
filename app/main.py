from fastapi import FastAPI
from pydantic import BaseModel
from typing import Annotated
from fastapi import Query
from app import data

class AccountFilter(BaseModel): # inherits BaseModel for data schema definition
    owner_id: str | None = None
    account_type: str | None = None
    min_balance_pence: int | None = None

app = FastAPI()

@app.get("/health")
def show_health():
    return {"status": "ok"}

@app.get("/accounts")
def get_accounts(f: Annotated[AccountFilter, Query()]): # Annotated[Type, metadata -> coming from: URL's query string]
    return data.find_accounts(owner_id=f.owner_id, account_type=f.account_type, min_balance_pence=f.min_balance_pence)

@app.post("/accounts/search")
def find_accounts(f: AccountFilter):
    return data.find_accounts(owner_id=f.owner_id, account_type=f.account_type, min_balance_pence=f.min_balance_pence)
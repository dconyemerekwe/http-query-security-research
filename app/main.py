from fastapi import FastAPI
from app import data

app = FastAPI()

@app.get("/health")
def show_health():
    return {"status": "ok"}

@app.get("/accounts")
def get_accounts(owner_id: str | None = None,
                 account_type: str | None = None,
                 min_balance_pence: int | None = None):
    return data.find_accounts(owner_id=owner_id,
                              account_type=account_type,
                              min_balance_pence=min_balance_pence)
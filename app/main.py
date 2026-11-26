from fastapi import FastAPI, Query, Depends, Header, Request
from pydantic import BaseModel
from typing import Annotated
from app import data, auth

class AccountFilter(BaseModel): # inherits BaseModel for data schema definition
    owner_id: str | None = None
    account_type: str | None = None
    min_balance_pence: int | None = None

CurrentUser = Annotated[str, Depends(auth.get_current_user)] # Annotated[Type, metadata]

app = FastAPI()

AUDITED_READ_METHODS = ("GET",) # simulating pre-existing read-audit control
CSRF_EXEMPT_METHODS = ("GET", "HEAD", "OPTIONS") # simulates a pre-existing CSRF protection control

@app.middleware("http")
async def tag_method_controls(request: Request, call_next):
    """
    Runs before the route, passes on the request, receives the route's response and tags its header based on request methods checks
    """
    response = await call_next(request)

    if request.method in AUDITED_READ_METHODS:
        response.headers["X-Read-Audit"] = "recorded"

    if request.method not in CSRF_EXEMPT_METHODS:
        response.headers["X-CSRF-Check"] = "required"

    return response

def search_owned_accounts(f: AccountFilter, user_id: str) -> list[dict]:
    if f.owner_id is not None and f.owner_id != user_id:
        return []

    return data.find_accounts(owner_id=user_id, account_type=f.account_type, min_balance_pence=f.min_balance_pence)

@app.get("/health")
def show_health():
    return {"status": "ok"}

@app.api_route("/accounts", methods=["QUERY"])
def query_accounts(f: AccountFilter, current_user: CurrentUser): 
    return search_owned_accounts(f, current_user)

@app.get("/accounts")
def get_accounts(f: Annotated[AccountFilter, Query()], current_user: CurrentUser): 
    return search_owned_accounts(f, current_user)

@app.post("/accounts/search")
def post_accounts(f: AccountFilter, current_user: CurrentUser):
    return search_owned_accounts(f, current_user)
from typing import Annotated
from fastapi import HTTPException, Header

VALID_TOKENS: dict[str, str] = {
    "alice-test-token-1": "u-001",
    "bob-test-token-2": "u-002"}

def get_current_user(authorisation: Annotated[str | None, Header()] = None):
    if authorisation not in VALID_TOKENS:
        raise HTTPException(status_code=401, detail="Not authenticated", headers={"WWW-Authenticate": "Bearer"})

    elif not authorisation.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated", headers={"WWW-Authenticate": "Bearer"})

    # check 3: token isn't one we know

    # success